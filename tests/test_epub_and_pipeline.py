import zipfile
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

from scan2kindle.epub import write_epub
from scan2kindle.models import Article, Block
from scan2kindle.pipeline import discover
from scan2kindle.render import find_gutter, render_book


def test_write_epub_contains_navigation_and_images(tmp_path: Path):
    figures = tmp_path / "figures"
    figures.mkdir()
    Image.new("L", (20, 30), 255).save(figures / "page_p0001.jpg")
    blocks = [
        Block("img", src="page_p0001.jpg", page=0),
        Block("h", "第一章", page=1),
        Block("p", "正文 & <测试>", page=1),
    ]
    out = tmp_path / "book.epub"
    sections = write_epub(out, "测试书", blocks, [Article(1, "第一章", "作者", 1)], figures, "id", author="作者")
    assert sections == 2
    with zipfile.ZipFile(out) as book:
        assert book.namelist()[0] == "mimetype"
        assert book.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        nav = book.read("OEBPS/nav.xhtml").decode()
        chapter = book.read("OEBPS/text/s002.xhtml").decode()
        assert "第一章　作者" in nav
        assert "正文 &amp; &lt;测试&gt;" in chapter
        assert "OEBPS/images/page_p0001.jpg" in book.namelist()


def test_find_gutter_on_two_page_spread():
    image = np.full((200, 400), 255, dtype=np.uint8)
    image[20:180, 20:190] = 0
    image[20:180, 215:380] = 0
    assert 190 <= find_gutter(image) <= 215


def test_render_splits_wide_scans(tmp_path: Path):
    pdf = tmp_path / "spread.pdf"
    document = pymupdf.open()
    page = document.new_page(width=800, height=500)
    page.draw_rect(pymupdf.Rect(30, 30, 380, 470), color=(0, 0, 0), fill=(0, 0, 0))
    page.draw_rect(pymupdf.Rect(420, 30, 770, 470), color=(0, 0, 0), fill=(0, 0, 0))
    document.save(pdf)
    images = render_book(pdf, tmp_path / "work", jobs=1, target_height=250)
    assert [p.name for p in images] == ["p0001a.png", "p0001b.png"]


def test_discover_skips_identical_pdfs(tmp_path: Path):
    (tmp_path / "a.pdf").write_bytes(b"same")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "b.pdf").write_bytes(b"same")
    (tmp_path / "c.PDF").write_bytes(b"different")
    assert [p.name for p in discover(tmp_path)] == ["a.pdf", "c.PDF"]
