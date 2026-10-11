"""Command-line interface for scan2kindle."""
from __future__ import annotations

import argparse
import os
import platform
import sys
from pathlib import Path

from . import __version__
from .pipeline import Options, run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scan2kindle",
        description="Convert scanned PDF books into reflowable EPUB and Kindle AZW3 files.",
    )
    parser.add_argument("input", type=Path, help="PDF file or folder containing PDFs")
    parser.add_argument("books", nargs="*", help="optional filename fragments to convert from the input folder")
    parser.add_argument("-o", "--output", type=Path, default=Path("output"), help="output folder (default: ./output)")
    parser.add_argument("--cache", type=Path, help="cache folder for page images and OCR (default: OUTPUT/.cache)")
    parser.add_argument("--azw3", action="store_true", help="also create AZW3 with Calibre")
    parser.add_argument("--force", action="store_true", help="rebuild books that already have an EPUB")
    parser.add_argument("--languages", default="zh-Hans,en-US", help="Vision OCR languages, comma separated")
    parser.add_argument("--book-language", default="zh-CN", help="EPUB language tag (default: zh-CN)")
    parser.add_argument("--author", default="", help="author metadata applied to every output book")
    parser.add_argument("--publisher", default="", help="publisher metadata applied to every output book")
    parser.add_argument("--pages", help="convert only a page range, for example 1-30")
    parser.add_argument("--jobs", type=int, default=max(2, (os.cpu_count() or 4) - 2), help="page rendering workers")
    parser.add_argument("--ocr-jobs", type=int, default=4, help="parallel OCR workers")
    parser.add_argument("--page-height", type=int, default=2200, help="rendered page height in pixels")
    parser.add_argument("--no-split-spreads", action="store_true", help="do not split wide two-page scans")
    parser.add_argument("--kindle-profile", default="kindle_pw3", help="Calibre output profile for AZW3")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if platform.system() != "Darwin":
        raise SystemExit("scan2kindle currently requires macOS because it uses Apple's Vision OCR.")
    source = args.input.expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"Input not found: {source}")
    if source.is_file():
        if source.suffix.lower() != ".pdf":
            raise SystemExit("Input file must be a PDF")
        input_dir = source.parent
        selection = [source.name]
    else:
        input_dir = source
        selection = args.books
    output = args.output.expanduser().resolve()
    options = Options(
        input_dir=input_dir,
        output_dir=output,
        cache_dir=(args.cache.expanduser().resolve() if args.cache else output / ".cache"),
        azw3=args.azw3,
        force=args.force,
        jobs=args.jobs,
        ocr_jobs=args.ocr_jobs,
        languages=args.languages,
        book_language=args.book_language,
        author=args.author,
        publisher=args.publisher,
        pages=args.pages,
        target_height=args.page_height,
        split_spreads=not args.no_split_spreads,
        kindle_profile=args.kindle_profile,
    )
    rows = run(options, selection)
    if any(str(row.get("status", "")).startswith("failed") for row in rows):
        sys.exit(1)
