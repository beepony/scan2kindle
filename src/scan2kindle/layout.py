"""Rebuild readable text structure from OCR line boxes.

This module handles page furniture removal, column ordering, headings,
paragraph continuation, figures, and contents-page navigation.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

from .models import Article, Block, Line

CJK = r"\u3400-\u9fff\uf900-\ufaff"
CJK_RE = re.compile(f"[{CJK}]")


PUNCT_MAP = {",": "，", ":": "：", ";": "；", "?": "？", "!": "！", "(": "（", ")": "）"}


def normalize_text(text: str) -> str:
    text = text.replace("⋯", "…")
    text = re.sub(r"(?:[…•·]\s*){2,}", "……", text)
    text = re.sub(r"…{3,}", "……", text)
    text = re.sub(r"[—–－-]{2,}|—[一-]|[一-]—", "——", text)

    # Vision occasionally emits ASCII punctuation inside Chinese prose.
    def repl(m: re.Match) -> str:
        return m.group(1) + PUNCT_MAP[m.group(2)] + m.group(3)

    text = re.sub(rf"([{CJK}“”‘’])([,:;?!()])([{CJK}“”‘’]?)", repl, text)
    return text.strip()


def join_text(a: str, b: str) -> str:
    if not a:
        return b
    if a[-1].isascii() and b[:1].isascii() and a[-1].isalnum() and b[:1].isalnum():
        return a + " " + b
    return a + b


def clean_header_key(text: str) -> str:
    return re.sub(r"\d+", "#", re.sub(r"\s+", "", text))


def parse_pages(ocr_pages: list[dict]) -> list[list[Line]]:
    pages = []
    for data in ocr_pages:
        lines = []
        for item in data.get("lines", []):
            text = normalize_text(item["text"])
            if text:
                x0, y0, x1, y1 = item["box"]
                lines.append(Line(text, float(item.get("conf", 1)), x0, y0, x1, y1))
        pages.append(lines)
    return pages


def repeated_margin_keys(pages: list[list[Line]], ocr_pages: list[dict]) -> set[str]:
    counts: Counter[str] = Counter()
    for lines, data in zip(pages, ocr_pages):
        h = data["height"]
        seen = set()
        for line in lines:
            if line.y1 < h * 0.075 or line.y0 > h * 0.925:
                key = clean_header_key(line.text)
                if 1 < len(key) <= 30:
                    seen.add(key)
        counts.update(seen)
    return {k for k, n in counts.items() if n >= 4}


def is_margin_noise(line: Line, page_h: float, repeated: set[str]) -> bool:
    compact = re.sub(r"\s+", "", line.text)
    if (line.y1 < page_h * 0.12 or line.y0 > page_h * 0.88) and re.fullmatch(r"[\divxlcIVXLC·•.\-—]{1,5}", compact):
        return True
    in_margin = line.y1 < page_h * 0.075 or line.y0 > page_h * 0.925
    return in_margin and clean_header_key(compact) in repeated


def order_columns(lines: list[Line], page_w: float) -> list[list[Line]]:
    """Return text columns in reading order for one- or two-column pages."""
    body = [l for l in lines if len(l.text) >= 4]
    if len(body) >= 12:
        # Find a vertical gutter crossed by few lines, then require text on both sides.
        best = None
        for x in np.linspace(page_w * 0.32, page_w * 0.68, 37):
            crossing = sum(1 for l in body if l.x0 < x - 8 and l.x1 > x + 8)
            left = [l for l in body if l.x1 <= x + 8]
            right = [l for l in body if l.x0 >= x - 8]
            score = crossing - min(len(left), len(right)) * 0.05
            if len(left) >= 5 and len(right) >= 5 and (best is None or score < best[0]):
                best = (score, x, crossing)
        if best and best[2] <= max(2, len(body) * 0.08):
            mid = best[1]
            above = [l for l in lines if l.x0 < mid - 8 and l.x1 > mid + 8]
            split_y = max((l.y1 for l in above), default=0)
            header = [l for l in lines if l.y1 <= split_y + 2]
            rest = [l for l in lines if l not in header]
            return [
                sorted(header, key=lambda l: (l.y0, l.x0)),
                sorted([l for l in rest if (l.x0 + l.x1) / 2 < mid], key=lambda l: (l.y0, l.x0)),
                sorted([l for l in rest if (l.x0 + l.x1) / 2 >= mid], key=lambda l: (l.y0, l.x0)),
            ]
    return [sorted(lines, key=lambda l: (l.y0, l.x0))]


def estimate_body_height(lines: list[Line], fallback: float) -> tuple[float, float]:
    """Estimate printed body-line height from full-width text lines."""
    long_lines = [l for l in lines if len(l.text) >= 12]
    if len(long_lines) < 6:
        return fallback, 0.0
    return float(np.median([l.h for l in long_lines])), 0.0

LEADER_RE = re.compile(r"\s*(?:[⋯…•·]+|\.{2,}|\s\.)\s*")

RANGE_RE = re.compile(r"^(\d{1,3})(?:\s*[-–—]\s*\d{1,3})?(?:\s+(.+))?$")

DESCRIPTION_RE = re.compile(r"[。！？；，]$|^[，。]|.{24,}")


def clean_toc_title(text: str) -> tuple[str, str]:
    parts = [p.strip(" |｜") for p in LEADER_RE.split(text) if p.strip(" |｜")]
    if not parts:
        return "", ""
    title = re.sub(r"^[•·.\s]+|[•·.\s]+$", "", parts[0])
    author = " ".join(parts[1:])
    if not author:
        m = re.match(r"(.+?)\s+([^\s]{1,8}(?:\s*/\s*[^\s]{1,8})?(?:\s+[^\s]{1,8})?)$", title)
        if m and not re.search(r"[《》“”：？]", m.group(2)):
            title, author = m.group(1), m.group(2)
    title = re.sub(r"^[【】|I1!！_\s]+", "", title).strip()
    return title, author


def toc_rows(lines: list[Line]) -> list[tuple[float, int, str]]:
    """Extract (y, printed_page, title) pairs from a contents page."""
    rows = []
    numbers = []
    texts = []
    for line in lines:
        m = RANGE_RE.match(line.text.strip())
        if m and m.group(2) and CJK_RE.search(m.group(2)):
            rows.append(((line.y0 + line.y1) / 2, int(m.group(1)), m.group(2)))
        elif m and not m.group(2):
            numbers.append((line, int(m.group(1))))
        elif CJK_RE.search(line.text):
            texts.append(line)

    used = set()
    number_x = np.median([n.x1 for n, _ in numbers]) if numbers else 0
    title_texts = [
        (i, t) for i, t in enumerate(texts)
        if t.x0 > number_x - 5 and not DESCRIPTION_RE.search(t.text) and not re.fullmatch(r"[目录|I•·\s]+", t.text)
    ]
    title_x = np.percentile([t.x0 for _, t in title_texts], 25) if title_texts else number_x
    for number_line, page_no in numbers:
        cy = (number_line.y0 + number_line.y1) / 2
        candidates = []
        for i, line in title_texts:
            if i in used or abs(line.x0 - title_x) > max(120, line.h * 3):
                continue
            dy = abs((line.y0 + line.y1) / 2 - cy)
            if dy < max(number_line.h, line.h) * 1.15:
                candidates.append((dy, line.x0, i, line))
        if candidates:
            _, _, i, line = min(candidates)
            used.add(i)
            # Some contents layouts put the author in a separate OCR box.
            line_cy = (line.y0 + line.y1) / 2
            same_row = [t for j, t in enumerate(texts) if j != i and abs((t.y0 + t.y1) / 2 - line_cy) < max(t.h, line.h) * 0.5 and t.x0 > line.x1 - 5]
            text = line.text + "".join(" " + t.text for t in sorted(same_row, key=lambda t: t.x0) if not DESCRIPTION_RE.search(t.text))
            rows.append((cy, page_no, text))
    return sorted(rows)


def parse_contents(pages: list[list[Line]]) -> tuple[list[Article], set[int]]:
    articles: list[Article] = []
    toc_pages: set[int] = set()
    started = False
    for index, lines in enumerate(pages[:24]):
        top_lines = sorted(lines, key=lambda l: l.y0)[:6]
        # Match a standalone contents heading, not the word "目录" inside body text.
        has_heading = any(
            re.fullmatch(r"(?:目\s*录|录\s*目|contents|table\s+of\s+contents)", l.text.strip(), re.I)
            for l in top_lines
        )
        rows = toc_rows(lines)
        if has_heading or (index < 12 and len(rows) >= 5):
            started = True
        elif started and len(rows) < 3:
            break
        if not started:
            continue
        toc_pages.add(index)
        for _, page_no, raw_title in rows:
            title, author = clean_toc_title(raw_title)
            if title and len(title) >= 2:
                articles.append(Article(page_no, title, author))
        # A contents page without a numbered first item usually starts at page 1.
        if index == min(toc_pages) and rows and rows[0][1] > 1:
            leader_lines = [l for l in lines if LEADER_RE.search(l.text) and l.y0 < rows[0][0]]
            if leader_lines:
                first = min(leader_lines, key=lambda l: l.y0)
                same_row = [l for l in lines if l is not first and abs((l.y0 + l.y1) / 2 - (first.y0 + first.y1) / 2) < first.h * 0.75]
                title, author = clean_toc_title(" ".join([first.text] + [l.text for l in sorted(same_row, key=lambda l: l.x0)]))
                if title:
                    articles.append(Article(1, title, author))

    unique: dict[int, Article] = {}
    for article in sorted(articles, key=lambda a: a.page):
        unique.setdefault(article.page, article)
    result = list(unique.values())
    return (result if len(result) >= 3 else []), toc_pages


def detect_page_offset(pages: list[list[Line]], ocr_pages: list[dict]) -> int | None:
    offsets: Counter[int] = Counter()
    for index, (lines, data) in enumerate(zip(pages, ocr_pages)):
        h = data["height"]
        for line in lines:
            if (line.y1 < h * 0.12 or line.y0 > h * 0.88) and re.fullmatch(r"\d{1,3}", line.text.strip()):
                offsets[int(line.text) - index] += 1
    if not offsets:
        return None
    offset, count = offsets.most_common(1)[0]
    if count < 5:
        return None
    # Split spreads use OCR images for each physical page; account for that.
    return offset


def norm_title(text: str) -> str:
    return re.sub(rf"[^{CJK}A-Za-z0-9]", "", text)


def is_name_line(text: str) -> bool:
    compact = norm_title(text)
    return 2 <= len(compact) <= 12 and not re.search(r"[。，！？：；《》“”]", text)


def match_contents_titles(pages: list[list[Line]], ocr_pages: list[dict], toc_pages: set[int], body_h: float) -> list[Article]:
    """Match titles from a contents page without page numbers to large headings."""
    if not toc_pages:
        return []
    toc_lines = []
    for index in sorted(toc_pages):
        toc_lines.extend(sorted(pages[index], key=lambda l: (l.y0, l.x0)))
    candidates: list[str] = []
    xs: list[float] = []
    for line in toc_lines:
        text = re.sub(r"^\d{1,3}\s+", "", line.text.strip())
        key = norm_title(text)
        if (
            2 <= len(key) <= 24
            and CJK_RE.search(text)
            and not DESCRIPTION_RE.search(text)
            and not text.startswith(("*", "＊"))
            and not re.search(r"目\s*录", text)
        ):
            candidates.append(text)
            xs.append(line.x0)
    if not candidates:
        return []

    first_body = max(toc_pages) + 1
    found: dict[int, int] = {}
    used_pages: set[int] = set()
    for pos, title in enumerate(candidates):
        key = norm_title(title)
        for index in range(first_body, len(pages)):
            if index in used_pages:
                continue
            h = ocr_pages[index]["height"]
            hit = False
            for line in pages[index]:
                line_key = norm_title(line.text)
                if line.y0 > h * 0.6 or line.h < body_h * 1.25 or not line_key:
                    continue
                if line_key == key or (len(key) >= 4 and len(line_key) >= 4 and (key in line_key or line_key in key)):
                    hit = True
                    break
            if hit:
                found[pos] = index
                used_pages.add(index)
                break
    articles: list[Article] = []
    if not found:
        return []
    # Use matched titles as the reference column, ignoring intro text on nearby pages.
    title_x = min(xs[pos] for pos in found)
    for pos, index in found.items():
        author = ""
        nxt = pos + 1
        # Authors are printed indented beneath the title on these contents pages.
        if nxt < len(candidates) and nxt not in found and xs[nxt] > xs[pos] + body_h and is_name_line(candidates[nxt]):
            author = candidates[nxt]
        if xs[pos] > title_x + body_h * 1.5:
            continue
        articles.append(Article(index, candidates[pos], author, index))
    return sorted(articles, key=lambda a: a.start)


def detect_article_openers(pages: list[list[Line]], ocr_pages: list[dict], body_h: float) -> list[Article]:
    """Find article opening pages: a large title above body text that starts low on the page."""
    articles = []
    for index, (lines, data) in enumerate(zip(pages, ocr_pages)):
        if index < 2:
            continue
        h = data["height"]
        ordered = sorted(lines, key=lambda l: l.y0)
        body = [l for l in ordered if len(l.text) >= 12]
        if len(body) < 5 or body[0].y0 < h * 0.3:
            continue
        top = [l for l in ordered if l.y1 <= body[0].y0 + 1 and l.y0 < h * 0.55]
        big = [l for l in top if l.h >= body_h * 1.45 and len(l.text) <= 30 and CJK_RE.search(l.text)]
        if not big:
            continue
        title_line = big[0]
        title = re.sub(r"^[【】|I1!！_\s]+|[®©]+$", "", title_line.text).strip()
        author = next((l.text for l in top if l is not title_line and l.y0 > title_line.y0 and is_name_line(l.text)), "")
        if len(norm_title(title)) >= 2:
            articles.append(Article(index, title, author, index))
    return articles if len(articles) >= 3 else []


def merge_same_row(lines: list[Line]) -> list[Line]:
    """Merge OCR fragments that Vision split on the same printed line."""
    rows: list[list[Line]] = []
    for line in sorted(lines, key=lambda l: (l.y0, l.x0)):
        if rows:
            prev = rows[-1][-1]
            overlap = min(prev.y1, line.y1) - max(prev.y0, line.y0)
            if overlap > min(prev.h, line.h) * 0.45:
                rows[-1].append(line)
                continue
        rows.append([line])

    merged: list[Line] = []
    for row in rows:
        row.sort(key=lambda l: l.x0)
        current = row[0]
        for line in row[1:]:
            text = line.text
            # Overlapping fragments often duplicate a closing quote or comma.
            if line.x0 < current.x1 and text[:1] and current.text.endswith(text[:1]):
                text = text[1:]
            current = Line(
                join_text(current.text, text),
                min(current.conf, line.conf),
                current.x0,
                min(current.y0, line.y0),
                max(current.x1, line.x1),
                max(current.y1, line.y1),
            )
        merged.append(current)
    return merged


def find_figures(image_path: Path, lines: list[Line], page_index: int, figure_dir: Path) -> list[tuple[float, float, Block]]:
    """Crop large non-text regions (photos/illustrations) from a page image."""
    img = Image.open(image_path).convert("L")
    w, h = img.size
    scale = 500 / max(w, h)
    small = img.resize((max(1, int(w * scale)), max(1, int(h * scale))))
    arr = np.asarray(small)
    ink = arr < 185
    sh, sw = ink.shape
    ink[: int(sh * 0.04), :] = False
    ink[int(sh * 0.96):, :] = False
    for line in lines:
        pad = line.h * 0.35
        x0 = max(0, int((line.x0 - pad) * scale))
        x1 = min(sw, int((line.x1 + pad) * scale) + 1)
        y0 = max(0, int((line.y0 - pad) * scale))
        y1 = min(sh, int((line.y1 + pad) * scale) + 1)
        ink[y0:y1, x0:x1] = False

    rows = ink.mean(axis=1) > 0.035
    runs = []
    start = None
    for y, flag in enumerate(np.append(rows, False)):
        if flag and start is None:
            start = y
        elif not flag and start is not None:
            if y - start >= sh * 0.09:
                runs.append((start, y))
            start = None

    figures = []
    for n, (ry0, ry1) in enumerate(runs):
        cols = np.where(ink[ry0:ry1].mean(axis=0) > 0.025)[0]
        if len(cols) < sw * 0.22:
            continue
        cx0, cx1 = cols.min(), cols.max() + 1
        if (cx1 - cx0) * (ry1 - ry0) < sw * sh * 0.035:
            continue
        box = (
            max(0, int(cx0 / scale) - 12),
            max(0, int(ry0 / scale) - 12),
            min(w, int(cx1 / scale) + 12),
            min(h, int(ry1 / scale) + 12),
        )
        crop = img.crop(box)
        crop.thumbnail((1072, 1448))
        name = f"fig_{page_index + 1:04d}_{image_path.stem}_{n + 1}.jpg"
        crop.save(figure_dir / name, quality=78, optimize=True, progressive=True)
        figures.append((box[1], box[3], Block("img", src=name, page=page_index)))
    return figures


def same_title(a: str, b: str) -> bool:
    norm = lambda s: re.sub(rf"[^{CJK}A-Za-z0-9]", "", s)
    a, b = norm(a), norm(b)
    return bool(a and b and (a in b or b in a))


def build_blocks(images: list[Path], ocr_pages: list[dict], figure_dir: Path) -> tuple[list[Block], list[Article], dict]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    pages = parse_pages(ocr_pages)
    all_lines = [l for page in pages for l in page]
    global_body_h, _ = estimate_body_height(all_lines, 30)
    articles, toc_pages = parse_contents(pages)
    offset = detect_page_offset(pages, ocr_pages)
    if articles and offset is not None:
        for article in articles:
            article.start = article.page - offset
        articles = [a for a in articles if 0 <= a.start < len(images)]
    else:
        articles = []
    toc_source = "contents" if articles else ""
    # Contents pages without page numbers: match their titles to article headings.
    if len(articles) < 5:
        matched = match_contents_titles(pages, ocr_pages, toc_pages, global_body_h)
        merged = list(articles)
        for article in matched:
            if not any(a.start == article.start or same_title(a.title, article.title) for a in merged):
                merged.append(article)
        if len(merged) >= 3 and len(merged) > len(articles):
            articles = sorted(merged, key=lambda a: a.start)
            toc_source = "contents+headings"
    # Issues without a contents page: detect article opening pages.
    if len(articles) < 3:
        openers = detect_article_openers(pages, ocr_pages, global_body_h)
        if openers:
            articles = openers
            toc_source = "openers"
    repeated = repeated_margin_keys(pages, ocr_pages)

    blocks: list[Block] = []
    stats = {
        "pages": len(images),
        "lines": 0,
        "low_conf": 0,
        "image_pages": 0,
        "figures": 0,
        "toc_entries": len(articles),
        "toc_source": toc_source,
        "page_offset": offset,
    }
    article_starts = {a.start for a in articles}
    for page_index, (image_path, data, raw_lines) in enumerate(zip(images, ocr_pages, pages)):
        page_w, page_h = data["width"], data["height"]
        lines = [l for l in raw_lines if not is_margin_noise(l, page_h, repeated)]
        text_chars = sum(len(l.text) for l in lines)
        stats["lines"] += len(lines)
        stats["low_conf"] += sum(1 for l in lines if l.conf < 0.45)
        body_h, slope = estimate_body_height(lines, global_body_h)

        # Covers, photo spreads and sparse decorative pages are kept as images.
        if text_chars < 45 or page_index < 2 or page_index in toc_pages:
            name = f"page_{image_path.stem}.jpg"
            img = Image.open(image_path).convert("L")
            img.thumbnail((1072, 1448))
            img.save(figure_dir / name, quality=78, optimize=True, progressive=True)
            blocks.append(Block("img", src=name, page=page_index))
            stats["image_pages"] += 1
            continue

        figures = find_figures(image_path, lines, page_index, figure_dir)
        entries: list[tuple[float, Block]] = [(y0, block) for y0, _, block in figures]
        stats["figures"] += len(figures)
        first_text_on_page = page_index not in article_starts
        for column in order_columns(lines, page_w):
            column = merge_same_row(column)
            long_lines = [l for l in column if len(l.text) >= 10]
            left = np.percentile([l.x0 for l in long_lines], 15) if long_lines else min((l.x0 for l in column), default=0)
            right = np.percentile([l.x1 for l in long_lines], 85) if long_lines else max((l.x1 for l in column), default=page_w)
            column_w = max(1.0, right - left)
            prev: Line | None = None
            current: Block | None = None
            for line in column:
                gap_before = line.y0 - prev.y1 if prev else line.y0
                eff_h = line.h - line.w * slope
                centered = abs((line.x0 + line.x1) / 2 - (left + right) / 2) < body_h * 1.5
                heading = (
                    (
                        eff_h >= body_h * 1.30
                        and len(line.text) <= 30
                        and line.w < column_w * 0.82
                        and gap_before > body_h * 0.45
                        and not re.search(r"[。；，、：]$", line.text)
                    )
                    # Section numbers such as 一 / 二 / 3 are often body-sized but centered.
                    or (centered and len(line.text) <= 6 and line.w < column_w * 0.35 and gap_before > body_h * 1.2)
                )
                near_figure = any(fy0 - body_h * 3 < line.y0 < fy1 + body_h * 3 for fy0, fy1, _ in figures)
                caption = near_figure and eff_h < body_h * 0.78 and len(line.text) <= 80
                # Quoted/oral-history passages are indented as a whole block;
                # compare with the previous line before treating it as a new paragraph.
                indent = line.x0 - left > body_h * 1.1 and (
                    prev is None or line.x0 - prev.x0 > body_h * 0.9 or prev.x1 < right - body_h * 1.6
                )
                gap = prev is not None and gap_before > max(body_h * 1.25, prev.h * 1.15)
                prev_right = right if prev is None or prev.x0 - left <= body_h * 1.1 else max(prev.x1, right - body_h * 3)
                short_prev = prev is not None and prev.x1 < prev_right - body_h * 1.6
                if heading:
                    if current and current.kind == "h" and prev and line.y0 - prev.y1 < body_h * 1.2:
                        current.text = join_text(current.text, line.text)
                        current.confs.append(line.conf)
                    else:
                        current = Block("h", line.text, page=page_index, confs=[line.conf])
                        entries.append((line.y0, current))
                elif caption:
                    if current and current.kind == "caption" and not gap:
                        current.text = join_text(current.text, line.text)
                    else:
                        current = Block("caption", line.text, page=page_index, confs=[line.conf])
                        entries.append((line.y0, current))
                elif current is None or current.kind != "p" or indent or gap or short_prev:
                    current = Block("p", line.text, page=page_index, confs=[line.conf])
                    # A non-indented first line usually continues the previous page.
                    current.continues = first_text_on_page and not indent
                    entries.append((line.y0, current))
                else:
                    current.text = join_text(current.text, line.text)
                    current.confs.append(line.conf)
                if current and current.kind in {"p", "h"}:
                    first_text_on_page = False
                prev = line
        # Two-column pages are ordered by column, figures by vertical position.
        text_entries = [e for e in entries if e[1].kind != "img"]
        fig_entries = sorted([e for e in entries if e[1].kind == "img"], key=lambda e: e[0])
        merged_page: list[Block] = []
        for y, block in text_entries:
            while fig_entries and fig_entries[0][0] <= y:
                merged_page.append(fig_entries.pop(0)[1])
            merged_page.append(block)
        merged_page.extend(b for _, b in fig_entries)

        for block in merged_page:
            if (
                block.kind == "p"
                and block.continues
                and blocks
                and blocks[-1].kind == "p"
                and not re.search(r"[。！？”」』）)]$", blocks[-1].text)
            ):
                blocks[-1].text = join_text(blocks[-1].text, block.text)
                blocks[-1].confs.extend(block.confs)
            else:
                blocks.append(block)
    stats["body_line_height"] = round(body_h, 1)
    return blocks, articles, stats
