"""Render PDF pages to grayscale images and split two-page spreads."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image


def find_gutter(gray: np.ndarray) -> int:
    """Find the whitest vertical band around the center of a two-page scan."""
    h, w = gray.shape
    lo, hi = int(w * 0.40), int(w * 0.60)
    ink = (gray[int(h * 0.08): int(h * 0.92), lo:hi] < 150).mean(axis=0)
    ink = np.convolve(ink, np.ones(15) / 15, mode="same")
    return lo + int(np.argmin(ink))


def render_page(args: tuple[str, int, str, int, bool]) -> list[str]:
    pdf_path, index, out_dir, target_height, split_spreads = args
    out = Path(out_dir)
    existing = sorted(out.glob(f"p{index + 1:04d}*.png"))
    if existing:
        return [str(p) for p in existing]

    doc = pymupdf.open(pdf_path)
    page = doc[index]
    zoom = target_height / page.rect.height
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), colorspace=pymupdf.csGRAY, alpha=False)
    img = Image.frombytes("L", (pix.width, pix.height), pix.samples)

    # Some scans contain left/right book pages on one PDF page.
    if split_spreads and img.width > img.height * 1.15:
        cut = find_gutter(np.asarray(img))
        parts = [img.crop((0, 0, cut, img.height)), img.crop((cut, 0, img.width, img.height))]
        names = [f"p{index + 1:04d}a.png", f"p{index + 1:04d}b.png"]
    else:
        parts = [img]
        names = [f"p{index + 1:04d}.png"]

    paths = []
    for part, name in zip(parts, names):
        target = out / name
        tmp = target.with_suffix(".tmp.png")
        part.save(tmp, optimize=False)
        tmp.replace(target)
        paths.append(str(target))
    return paths


def render_book(
    pdf: Path,
    work: Path,
    jobs: int,
    pages: list[int] | None = None,
    target_height: int = 2200,
    split_spreads: bool = True,
) -> list[Path]:
    img_dir = work / "pages"
    img_dir.mkdir(parents=True, exist_ok=True)
    count = pymupdf.open(pdf).page_count
    indices = pages if pages is not None else list(range(count))
    tasks = [(str(pdf), i, str(img_dir), target_height, split_spreads) for i in indices]
    result: dict[int, list[str]] = {}
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for i, paths in zip(indices, pool.map(render_page, tasks, chunksize=4)):
            result[i] = paths
    return [Path(p) for i in indices for p in result[i]]
