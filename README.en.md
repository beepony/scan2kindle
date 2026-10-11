# scan2kindle

Convert **scanned PDF books** into **reflowable EPUB** and **Kindle AZW3** files.

[简体中文](README.md)

Many scanned PDFs are just page images, so text stays tiny on a Kindle and cannot be resized. `scan2kindle` uses OCR, rebuilds paragraphs and navigation, and keeps important images so scanned books are readable on e-ink devices.

> Platform: macOS. OCR uses Apple's built-in Vision framework and runs offline.

## Install with an AI agent

If you use Codex, Claude Code, or another agent that can operate your computer, copy the full prompt below and paste it into the agent. It checks your Mac, installs the tool, creates a PDF folder, runs a test conversion after you add PDFs, and then converts the whole folder.

> The prompt processes files locally and does not upload books. Installing developer tools, Python, or Calibre may require you to approve a system prompt or enter your Mac password.

<details>
<summary><strong>Show and copy the agent prompt</strong></summary>

````text
Please install the open-source tool scan2kindle on this Mac and guide me through my first conversion.

Project: https://github.com/beepony/scan2kindle

It converts scanned PDF books into Kindle-friendly EPUB and AZW3 files.

Please run the steps you can complete automatically, and keep me updated in simple, clear English. Stop and ask me only when I need to click a confirmation, enter a password, add PDFs, or choose an installation method.

## Ground rules

- This tool currently supports macOS only. If this computer is not running macOS, stop and explain why.
- Do not modify, move, delete, or upload my original PDFs.
- Convert only books I have the legal right to use.
- Do not upload any PDFs, EPUBs, AZW3 files, or recognized text.
- Do not use sudo unless you first explain why and get my permission.
- If a command fails because of permissions, sandboxing, or network restrictions, request permission according to your agent's rules and retry. Do not bypass restrictions.
- Do not install the tool inside the folder that contains my PDFs.

## 1. Check the computer

1. Confirm that the system is macOS.
2. Check whether git and swiftc are available:
   - If they are missing, run `xcode-select --install`.
   - Tell me to click "Install" in the window that appears.
   - Wait until I say the installation is complete.
3. Find Python 3.10 or newer:
   - Note: the python3 included with macOS may be version 3.9, which is too old.
   - If no suitable Python is available and Homebrew is installed, run `brew install python@3.12`.
   - If Homebrew is not installed, explain the installation options to me before continuing.
4. Check for Calibre's ebook-convert:
   - Look for it in PATH or at `/Applications/calibre.app/Contents/MacOS/ebook-convert`.
   - If it is missing and Homebrew is installed, run `brew install --cask calibre`.
   - If Calibre cannot be installed, continue with EPUB only. AZW3 output requires Calibre.

## 2. Install scan2kindle

1. If `~/scan2kindle` does not exist, download the tool from GitHub:

```zsh
git clone https://github.com/beepony/scan2kindle.git ~/scan2kindle
```

2. If `~/scan2kindle` already exists and is this repository, run `git pull --ff-only` to update it. If it is a different folder, ask me what to do.
3. Create an isolated Python environment. Replace `<Python 3.10+ path>` with the Python you found:

```zsh
cd ~/scan2kindle
<Python 3.10+ path> -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[test]'
```

4. Check the installation:

```zsh
.venv/bin/scan2kindle --version
.venv/bin/python -m pytest -q
```

## 3. Prepare the working folders

Create these folders:

```zsh
mkdir -p "$HOME/Kindle Conversion/PDFs to Convert"
mkdir -p "$HOME/Kindle Conversion/Output"
mkdir -p "$HOME/Kindle Conversion/Test Conversion"
```

Then open `$HOME/Kindle Conversion/PDFs to Convert` in Finder.

Tell me:

- Put the scanned PDFs you want to convert into the "PDFs to Convert" folder.
- You can create subfolders such as "2024" or "History"; the output will keep the same structure.
- If the original PDFs are important, copy them into this folder and keep the originals elsewhere.
- Reply "Ready" after adding the PDFs.

Continue only after I reply "Ready".

## 4. Test one book first

1. Find all PDFs in "PDFs to Convert" and its subfolders. Tell me how many there are and their total size.
2. Choose the first PDF and convert only its first 30 pages into the "Test Conversion" folder, so the test does not affect the final output.
3. If Calibre is installed, run:

```zsh
cd ~/scan2kindle
.venv/bin/scan2kindle "<full path to the first PDF>" -o "$HOME/Kindle Conversion/Test Conversion" --pages 1-30 --azw3 --force
```

4. If Calibre is not installed, remove `--azw3`.
5. The first run compiles the macOS text-recognition helper. If you see `Foundation._GenericObjCError` or a similar error, it is usually caused by your agent's restrictions. Request permission to run outside those restrictions and retry.
6. After the test succeeds, tell me:
   - where the EPUB and AZW3 files are;
   - how many characters were recognized;
   - how many navigation entries were created;
   - whether anything looks clearly wrong.
7. If epubcheck is installed, validate the test EPUB.

## 5. Convert the whole folder

After the test succeeds, start the full conversion and keep the Mac awake:

```zsh
cd ~/scan2kindle
caffeinate -dimsu .venv/bin/scan2kindle "$HOME/Kindle Conversion/PDFs to Convert" -o "$HOME/Kindle Conversion/Output" --azw3 2>&1 | tee -a "$HOME/Kindle Conversion/Output/conversion-log.txt"
```

If Calibre is not installed, remove `--azw3`.

During the conversion:

- Tell me from time to time how many books are finished. Do not flood the chat with the full log.
- If the conversion stops, run the same command again. Finished books are skipped, and recognized pages are reused.
- Do not use `--force` unless I ask you to rebuild existing books.

## 6. After the conversion

1. Review `$HOME/Kindle Conversion/Output/conversion-report.csv` and tell me:
   - how many books succeeded, were skipped, or failed;
   - which books have unusually few recognized characters;
   - which books have very few navigation entries;
   - which books have lower recognition confidence.
2. If possible, validate all EPUB files with epubcheck.
3. Open `$HOME/Kindle Conversion/Output` in Finder.
4. Explain in simple terms:
   - EPUB files are in "Output/EPUB" and are best for Send to Kindle;
   - AZW3 files are in "Output/AZW3" and can be copied over USB to the Kindle's documents folder;
   - to convert more PDFs later, I only need to add them to "PDFs to Convert" and ask you to run the same full-folder command again.

Finally, remind me that OCR may still contain a few mistakes, and complex tables, formulas, vertical text, and unusual layouts may be kept as images. I should check a few books on my Kindle before deleting any original PDFs.
````

</details>

You can also open the prompt file directly: [prompts/agent-install.en.md](prompts/agent-install.en.md)

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
