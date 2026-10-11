# scan2kindle

Convert **scanned PDF books** into **reflowable EPUB** and **Kindle AZW3** files.

[简体中文](README.md)

Many scanned PDFs are just page images, so text stays tiny on a Kindle and cannot be resized. `scan2kindle` uses OCR, rebuilds paragraphs and navigation, and keeps important images so scanned books are readable on e-ink devices.

> Platform: macOS. OCR uses Apple's built-in Vision framework and runs offline.

## Features

- Batch-convert PDFs recursively while preserving folder structure.
- Offline OCR with macOS Vision; Simplified Chinese and English by default.
- Split two-page scans stored as one wide PDF page.
- Remove running headers and page numbers; handle one- and two-column pages.
- Rebuild paragraphs across lines and pages; detect headings, bylines, figures, and captions.
- Build EPUB navigation from scanned contents pages, or match article opening headings when page numbers or contents pages are missing.
- Keep covers, contents pages, and image-heavy pages as images.
- Write EPUB 3 and optionally AZW3 through Calibre.
- Cache rendered pages and OCR so interrupted batches can resume.
- Skip byte-identical duplicate PDFs and write a CSV report.

## Install

Requirements: macOS 13+, Python 3.10+, Xcode Command Line Tools, and optionally Calibre for AZW3 output.

```zsh
xcode-select --install
brew install --cask calibre
git clone https://github.com/beepony/scan2kindle.git
cd scan2kindle
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

## Usage

```zsh
.venv/bin/scan2kindle ~/Books/scans -o ~/Books/kindle --azw3
.venv/bin/scan2kindle ~/Books/scans/book.pdf -o /tmp/test --pages 1-30
.venv/bin/scan2kindle ~/Books/scans --languages en-US --book-language en
```

Use `--force` to rebuild existing books and `--no-split-spreads` to keep wide pages intact. Run `scan2kindle --help` for all options.

Output files are written to `EPUB/`, `AZW3/`, and `conversion-report.csv`. Send EPUB files with Send to Kindle, or copy AZW3 files to the Kindle `documents` folder over USB.

See [docs/workflow.en.md](docs/workflow.en.md) for the full pipeline.

## Limitations

OCR can still contain mistakes. Complex tables, formulas, vertical text, and unusual layouts are usually kept as images. Navigation quality depends on how clearly the scanned book marks its contents and headings.

## Copyright

This project contains no books. Convert only files you have the right to use, and do not upload copyrighted PDFs or ebooks.

## License

[MIT](LICENSE)
