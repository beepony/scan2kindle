# scan2kindle

**Turn image-only scanned PDFs into Kindle-ready EPUB and AZW3 books with resizable text and clickable contents.**

[![Tests](https://github.com/beepony/scan2kindle/actions/workflows/test.yml/badge.svg)](https://github.com/beepony/scan2kindle/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)

[简体中文](README.md) · [Install with AI](#install-with-ai) · [Quick start](#quick-start) · [How it works](docs/workflow.en.md)

```text
Scanned PDF  ->  offline OCR + layout rebuild  ->  EPUB 3 with contents  ->  AZW3
```

## Why scan2kindle

Most tools make PDFs searchable or make PDF pages fit an e-reader. scan2kindle focuses on a different job: **rebuilding a scanned book as a real ebook.**

| Tool | Main output | Difference for scanned-book-to-Kindle conversion |
| --- | --- | --- |
| [Calibre](https://manual.calibre-ebook.com/conversion.html#convert-pdf-documents) | EPUB / AZW3 | Its manual calls PDF a poor input format, with limited support for image-based PDFs, columns, and contents |
| [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) | Searchable PDF | Adds a text layer for search and copy, but keeps a fixed-layout PDF |
| [k2pdfopt](https://www.willus.com/k2pdfopt/) | Kindle-optimized PDF | Crops and rearranges page images, preserving the look without EPUB navigation |
| [Marker](https://github.com/datalab-to/marker) | Markdown / JSON / HTML | Strong general document extraction, not focused on Kindle ebook output |
| **scan2kindle** | **EPUB 3 + AZW3** | **OCR, layout rebuild, contents, figures, and batch conversion in one pipeline** |

## Highlights

- **Truly reflowable**: rebuilds paragraphs in reading order, so text can be resized on Kindle.
- **Clickable contents**: reads scanned contents pages, including page offsets, unnumbered entries, and books with no contents page.
- **Built for real scans**: splits two-page spreads, handles one- and two-column pages, removes headers and page numbers, and joins paragraphs across pages.
- **Keeps what matters**: preserves covers, contents pages, figures, and captions; complex pages stay as images.
- **Offline and private**: uses macOS Vision OCR with strong Chinese support, no model downloads, no GPU, and no uploads.
- **Batch-ready**: converts folders recursively, resumes from cache, skips duplicate PDFs, and writes a quality report.

Real-world run: 121 Chinese scanned periodicals (about 4.7 GB), around 0.9 seconds per page and under a minute for a typical 320-page issue. Every EPUB passed EPUBCheck.

## Install with AI

Paste the prompt below into Codex, Claude Code, or another agent that can operate your computer. It installs the tool, creates a PDF folder, waits for your files, runs a test conversion, and then converts the batch.

> Files are processed locally and books are never uploaded. Installing developer tools, Python, or Calibre may require your approval or Mac password.

<details>
<summary><strong>Show and copy the AI install prompt</strong></summary>

````text
Please install https://github.com/beepony/scan2kindle on this Mac and guide me through my first scanned-PDF-to-Kindle conversion.

Do every step you can automatically and report progress briefly. Ask me only when I need to approve something, enter a password, or add PDFs.

Rules:
- macOS only. Do not modify, delete, or upload my PDFs or converted books.
- Do not use sudo. If permissions or sandboxing block a command, request access according to your agent's rules.

Steps:
1. Check the environment: Xcode Command Line Tools and Python 3.10+. Install Calibre if AZW3 output is wanted. Prefer Homebrew for missing tools when it is available.
2. Install the tool:
   - Clone or update the repo at `~/scan2kindle`.
   - Create `.venv` with Python 3.10+.
   - Run `.venv/bin/python -m pip install -e '.[test]'`.
   - Run the tests to confirm the install.
3. Create `~/Kindle Conversion/PDF Inbox`, `~/Kindle Conversion/Output`, and `~/Kindle Conversion/Test`, then open the inbox in Finder. Ask me to add PDFs (subfolders are fine) and wait until I reply "done".
4. Test the first 30 pages of one PDF:

```zsh
cd ~/scan2kindle
.venv/bin/scan2kindle "<PDF path>" -o "$HOME/Kindle Conversion/Test" --pages 1-30 --azw3 --force
```

5. If the test works, convert the whole folder:

```zsh
cd ~/scan2kindle
caffeinate -dimsu .venv/bin/scan2kindle "$HOME/Kindle Conversion/PDF Inbox" -o "$HOME/Kindle Conversion/Output" --azw3
```

Remove `--azw3` from both commands if Calibre is not installed. If the batch stops, run the same command again to resume.

6. When finished, review `conversion-report.csv`, tell me which books succeeded, failed, or need a quick check, and open the output folder. Explain:
   - Send files from `EPUB` with Send to Kindle.
   - Copy files from `AZW3` to the Kindle `documents` folder over USB.
````

</details>

You can also copy it from [prompts/agent-install.en.md](prompts/agent-install.en.md).

## Quick start

Requires macOS 13+, Python 3.10+, and Xcode Command Line Tools. AZW3 output also needs [Calibre](https://calibre-ebook.com/).

```zsh
xcode-select --install
brew install --cask calibre       # optional: AZW3 output
git clone https://github.com/beepony/scan2kindle.git
cd scan2kindle
python3 -m venv .venv             # python3 must be 3.10 or newer
.venv/bin/python -m pip install -e .
```

Test the first 30 pages of one book:

```zsh
.venv/bin/scan2kindle ~/Books/scans/book.pdf -o /tmp/s2k-test --pages 1-30 --azw3
```

Convert a whole folder:

```zsh
.venv/bin/scan2kindle ~/Books/scans -o ~/Books/kindle --azw3
```

Prefer not to use Terminal? Double-click `scripts/convert-folder.command` and choose a PDF folder.

## Output and Kindle transfer

```text
kindle/
├── EPUB/                  # send with Send to Kindle
├── AZW3/                  # copy to Kindle's documents folder over USB
├── conversion-report.csv  # pages, characters, contents entries, OCR quality
└── .cache/                # OCR cache for resuming
```

## Common options

| Option | Use |
| --- | --- |
| `--azw3` | Also create AZW3 (requires Calibre) |
| `--pages 1-30` | Convert selected pages for a quick test |
| `--languages en-US` | Set OCR languages |
| `--book-language en` | Set the ebook language |
| `--force` | Rebuild existing books |
| `--no-split-spreads` | Keep wide scanned pages intact |

See every option with `.venv/bin/scan2kindle --help`.

## Notes

- OCR may still contain small errors; complex tables, formulas, and vertical text are usually kept as images.
- macOS only for now.
- This project contains no books. Convert only files you have the right to use, and do not upload or share copyrighted books.

## License

[MIT](LICENSE)
