"""Batch orchestration: discover PDFs, convert them, and write a report."""
from __future__ import annotations

import csv
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from .epub import convert_azw3, write_epub
from .layout import build_blocks
from .ocr import ensure_ocr_binary, ocr_book
from .render import render_book

REPORT_FIELDS = [
    "time", "title", "source", "status", "epub", "azw3", "seconds", "pages", "chars", "sections",
    "toc_entries", "toc_source", "page_offset", "image_pages", "figures", "lines", "low_conf",
    "body_line_height",
]


@dataclass
class Options:
    input_dir: Path
    output_dir: Path
    cache_dir: Path
    azw3: bool = False
    force: bool = False
    jobs: int = 4
    ocr_jobs: int = 4
    languages: str = "zh-Hans,en-US"
    book_language: str = "zh-CN"
    author: str = ""
    publisher: str = ""
    pages: str | None = None
    target_height: int = 2200
    split_spreads: bool = True
    kindle_profile: str = "kindle_pw3"


def log(message: str) -> None:
    print(time.strftime("%H:%M:%S"), message, flush=True)


def file_hash(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover(input_dir: Path, selection: list[str] | None = None, exclude: Path | None = None) -> list[Path]:
    """Find PDFs recursively and skip byte-identical duplicates."""
    pdfs = sorted(p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf")
    if exclude:
        pdfs = [p for p in pdfs if exclude not in p.parents]
    unique: dict[str, Path] = {}
    for pdf in pdfs:
        unique.setdefault(file_hash(pdf), pdf)
    pdfs = sorted(unique.values())
    if not selection:
        return pdfs
    chosen = []
    for item in selection:
        matches = [p for p in pdfs if item in p.name or item == p.stem]
        if not matches:
            raise SystemExit(f"No PDF matches: {item}")
        chosen.extend(matches)
    return list(dict.fromkeys(chosen))


def output_paths(pdf: Path, options: Options) -> tuple[Path, Path]:
    try:
        relative = pdf.relative_to(options.input_dir).with_suffix("")
    except ValueError:
        relative = Path(pdf.stem)
    return options.output_dir / "EPUB" / relative.with_suffix(".epub"), options.output_dir / "AZW3" / relative.with_suffix(".azw3")


def parse_page_range(value: str | None, page_count: int) -> list[int] | None:
    if not value:
        return None
    first, last = [int(x) for x in value.split("-", 1)]
    if first < 1 or last < first or last > page_count:
        raise ValueError(f"Invalid page range {value}; this PDF has {page_count} pages")
    return list(range(first - 1, last))


def convert_pdf(pdf: Path, options: Options, ocr_bin: Path) -> dict:
    title = pdf.stem
    source = str(pdf)
    epub, azw3 = output_paths(pdf, options)
    if epub.exists() and not options.force:
        log(f"Skip existing: {epub}")
        return {"title": title, "source": source, "status": "skipped", "epub": str(epub)}

    started = time.time()
    log(f"Start: {pdf}")
    work = options.cache_dir / "books" / f"{pdf.stem[:40]}_{file_hash(pdf)[:12]}"
    with pymupdf.open(pdf) as document:
        page_count = document.page_count
    page_list = parse_page_range(options.pages, page_count)
    images = render_book(pdf, work, options.jobs, page_list, options.target_height, options.split_spreads)
    log(f"  Rendered {len(images)} page images")
    ocr_pages = ocr_book(images, work, options.ocr_jobs, ocr_bin, options.languages, log)
    blocks, articles, stats = build_blocks(images, ocr_pages, work / "figures")
    sections = write_epub(
        epub,
        title,
        blocks,
        articles,
        work / "figures",
        identifier=file_hash(pdf),
        author=options.author,
        language=options.book_language,
        publisher=options.publisher,
    )
    made_azw3 = convert_azw3(epub, azw3, options.kindle_profile) if options.azw3 else False
    if options.azw3 and not made_azw3:
        log("  Calibre was not found; AZW3 was skipped")
    elapsed = time.time() - started
    result = {
        "title": title,
        "source": source,
        "status": "done",
        "epub": str(epub),
        "azw3": str(azw3) if made_azw3 else "",
        "seconds": round(elapsed),
        **stats,
        "sections": sections,
        "chars": sum(len(block.text) for block in blocks if block.kind != "img"),
    }
    (work / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Done: {title} in {elapsed / 60:.1f} min, {result['chars']} chars, {sections} sections")
    return result


def write_report(rows: list[dict], output_dir: Path) -> Path:
    report = output_dir / "conversion-report.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with report.open("a", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDS, extrasaction="ignore")
        if handle.tell() == 0:
            writer.writeheader()
        writer.writerows({"time": stamp, **row} for row in rows)
    return report


def run(options: Options, selection: list[str] | None = None) -> list[dict]:
    ocr_bin = ensure_ocr_binary(options.cache_dir)
    excluded = options.output_dir if options.output_dir.is_relative_to(options.input_dir) else None
    rows = []
    for pdf in discover(options.input_dir, selection, excluded):
        try:
            rows.append(convert_pdf(pdf, options, ocr_bin))
        except Exception as exc:  # Keep long batches moving and report failures.
            log(f"Failed: {pdf}: {exc}")
            rows.append({"title": pdf.stem, "source": str(pdf), "status": f"failed: {exc}"})
    report = write_report(rows, options.output_dir)
    log(f"Report: {report}")
    return rows
