#!/bin/zsh
# Double-click to choose a folder of scanned PDFs and convert it.
set -u
cd "$(dirname "$0")/.." || exit 1

if [[ ! -x .venv/bin/scan2kindle ]]; then
  echo "First run: installing scan2kindle into .venv ..."
  python3 -m venv .venv && .venv/bin/python -m pip install -e . || exit 1
fi

input=$(osascript -e 'POSIX path of (choose folder with prompt "Choose a folder containing scanned PDF books")') || exit 1
output="${input%/}/scan2kindle-output"
mkdir -p "$output"
caffeinate -dimsu .venv/bin/scan2kindle "$input" -o "$output" --azw3 2>&1 | tee -a "$output/conversion-log.txt"
exit_status=${pipestatus[1]}
echo
echo "Output: $output"
read -k 1 "?Press any key to close..."
exit $exit_status
