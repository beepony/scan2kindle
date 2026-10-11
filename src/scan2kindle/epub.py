"""Write EPUB 3 packages and optional Kindle AZW3 files."""
from __future__ import annotations

import html
import re
import shutil
import subprocess
import time
import uuid
import zipfile
from pathlib import Path

from .layout import same_title
from .models import Article, Block


CSS = """
body { margin: 0 4%; font-family: serif; line-height: 1.62; text-align: justify; }
p { margin: 0; text-indent: 2em; }
h1, h2 { font-family: sans-serif; line-height: 1.35; text-align: center; page-break-after: avoid; }
h1 { font-size: 1.45em; margin: 1.6em 0 1em; }
h2 { font-size: 1.15em; margin: 1.4em 0 .8em; }
figure { margin: 1em 0; text-align: center; page-break-inside: avoid; }
img { max-width: 100%; max-height: 95vh; }
.page-image { margin: 0; }
.page-image img { width: 100%; }
.caption { font-size: .82em; line-height: 1.4; text-indent: 0; text-align: center; margin: .2em 0 1em; color: #444; }
.author { text-indent: 0; text-align: center; margin: -.4em 0 1.6em; color: #444; }
.deck { text-indent: 0; margin: 0 1.5em 1.8em; font-size: .92em; color: #444; }
"""


def xhtml(title: str, body: str, language: str = "zh-CN") -> str:
    lang = html.escape(language)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}" xml:lang="{lang}">
<head><meta charset="utf-8"/><title>{html.escape(title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>{body}</body></html>
"""


def split_sections(
    blocks: list[Block], articles: list[Article], front_title: str = "封面与目录"
) -> list[tuple[str, str, list[Block]]]:
    """Split by the scanned contents page; fall back to detected headings."""
    if articles:
        sections: list[tuple[str, str, list[Block]]] = [(front_title, "", [])]
        starts = sorted(articles, key=lambda a: a.start)
        pos = 0
        for block in blocks:
            while pos < len(starts) and block.page >= starts[pos].start:
                sections.append((starts[pos].title, starts[pos].author, []))
                pos += 1
            name = sections[-1][0]
            if block.kind == "h" and same_title(block.text, name):
                continue
            author = sections[-1][1]
            first_text = not any(b.kind in {"p", "caption"} for b in sections[-1][2])
            if first_text and block.kind == "p" and author and same_title(block.text, author):
                continue
            if first_text and block.kind == "p" and not author and len(block.text) <= 12 and not re.search(r"[。，！？：]", block.text):
                block.kind = "byline"
            if first_text and block.kind == "p" and len(block.text) <= 60 and block.text.endswith(("。", "？", "！")):
                block.kind = "deck"
            sections[-1][2].append(block)
        return [s for s in sections if s[2] or s[0] != front_title]

    sections = [(front_title, "", [])]
    for block in blocks:
        body_size = sum(len(b.text) for b in sections[-1][2] if b.kind == "p")
        if block.kind == "h" and body_size > 1200 and len(block.text) >= 2:
            sections.append((block.text, "", []))
            continue
        sections[-1][2].append(block)
    return [s for s in sections if s[2]]


def render_blocks(blocks: list[Block]) -> str:
    parts = []
    for block in blocks:
        if block.kind == "h":
            parts.append(f"<h2>{html.escape(block.text)}</h2>")
        elif block.kind == "img":
            cls = ' class="page-image"' if block.src.startswith("page_") else ""
            parts.append(f'<figure{cls}><img src="images/{html.escape(block.src)}" alt=""/></figure>')
        elif block.kind == "caption":
            parts.append(f'<p class="caption">{html.escape(block.text)}</p>')
        elif block.kind == "deck":
            parts.append(f'<p class="deck">{html.escape(block.text)}</p>')
        elif block.kind == "byline":
            parts.append(f'<p class="author">{html.escape(block.text)}</p>')
        else:
            parts.append(f"<p>{html.escape(block.text)}</p>")
    return "\n".join(parts)


def write_epub(
    path: Path,
    title: str,
    blocks: list[Block],
    articles: list[Article],
    figure_dir: Path,
    identifier: str,
    author: str = "",
    language: str = "zh-CN",
    publisher: str = "",
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.epub")
    book_uuid = uuid.uuid5(uuid.NAMESPACE_URL, identifier)
    sections = split_sections(blocks, articles, "Front matter" if not language.lower().startswith("zh") else "封面与目录")
    used_images = sorted({b.src for b in blocks if b.kind == "img"})
    cover = next((b.src for b in blocks if b.kind == "img"), None)
    modified = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="css" href="style.css" media-type="text/css"/>']
    spine = []
    nav_items = []
    with zipfile.ZipFile(tmp, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>""", compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/style.css", CSS, compress_type=zipfile.ZIP_DEFLATED)
        for n, (name, author, items) in enumerate(sections, 1):
            href = f"text/s{n:03d}.xhtml"
            heading = ""
            if n > 1:
                heading = f"<h1>{html.escape(name)}</h1>"
                if author:
                    heading += f'<p class="author">{html.escape(author)}</p>'
            z.writestr(f"OEBPS/{href}", xhtml(name, heading + render_blocks(items), language).replace('href="style.css"', 'href="../style.css"').replace('src="images/', 'src="../images/'), compress_type=zipfile.ZIP_DEFLATED)
            manifest.append(f'<item id="s{n:03d}" href="{href}" media-type="application/xhtml+xml"/>')
            spine.append(f'<itemref idref="s{n:03d}"/>')
            label = f"{name}　{author}" if author else name
            nav_items.append(f'<li><a href="{href}">{html.escape(label)}</a></li>')
        for n, name in enumerate(used_images, 1):
            z.write(figure_dir / name, f"OEBPS/images/{name}", compress_type=zipfile.ZIP_STORED)
            props = ' properties="cover-image"' if name == cover else ""
            manifest.append(f'<item id="img{n:04d}" href="images/{html.escape(name)}" media-type="image/jpeg"{props}/>')
        nav_title = "目录" if language.lower().startswith("zh") else "Contents"
        nav = xhtml(nav_title, f'<nav epub:type="toc" id="toc"><h1>{nav_title}</h1><ol>{"".join(nav_items)}</ol></nav>', language)
        z.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
        cover_meta = '<meta name="cover" content="img0001"/>' if cover == used_images[0] else ""
        creator = f"<dc:creator>{html.escape(author)}</dc:creator>" if author else ""
        publisher_xml = f"<dc:publisher>{html.escape(publisher)}</dc:publisher>" if publisher else ""
        opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="{html.escape(language)}">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">urn:uuid:{book_uuid}</dc:identifier><dc:title>{html.escape(title)}</dc:title>
{creator}<dc:language>{html.escape(language)}</dc:language>{publisher_xml}
<meta property="dcterms:modified">{modified}</meta>{cover_meta}
</metadata><manifest>{''.join(manifest)}</manifest><spine>{''.join(spine)}</spine></package>"""
        z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
    tmp.replace(path)
    return len(sections)


def find_ebook_convert() -> str | None:
    tool = shutil.which("ebook-convert") or "/Applications/calibre.app/Contents/MacOS/ebook-convert"
    return tool if Path(tool).exists() else None


def convert_azw3(epub: Path, azw3: Path, profile: str = "kindle_pw3") -> bool:
    tool = find_ebook_convert()
    if not tool:
        return False
    azw3.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([tool, str(epub), str(azw3), "--output-profile", profile, "--no-inline-toc"], check=True,
                   stdout=subprocess.DEVNULL)
    return True
