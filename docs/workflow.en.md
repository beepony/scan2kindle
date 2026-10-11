# Pipeline overview

1. **Discover PDFs** recursively and skip byte-identical duplicates.
2. **Render pages** to grayscale images, 2200 px high by default.
3. **Split spreads** when a page is much wider than it is tall, using the whitest gutter near the center.
4. **Run OCR** with macOS Vision. Every page is cached as JSON with text, confidence, and bounding boxes.
5. **Rebuild layout** by removing headers and page numbers, ordering one- or two-column text, merging line fragments, and rebuilding paragraphs across lines and pages.
6. **Detect structure**: large headings, bylines, decks, figures, and captions. Covers, contents pages, and sparse image-heavy pages are kept as full-page images.
7. **Create navigation** in this order:
   - parse numbered contents pages and infer the printed-page offset;
   - match unnumbered contents titles to large headings in the book;
   - detect article opening pages when no contents page exists;
   - fall back to detected headings.
8. **Write EPUB 3** with semantic chapters, navigation, CSS for Chinese reading, and embedded images.
9. **Create AZW3** with Calibre when `--azw3` is used.
10. **Report results** in `conversion-report.csv` for quality checks.

Recommended review loop: test with `--pages 1-30`, inspect the report and navigation, validate with EPUBCheck, then rebuild with `--force`. Cached OCR makes rebuilds fast.
