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
