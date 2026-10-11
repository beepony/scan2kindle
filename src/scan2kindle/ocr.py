"""macOS Vision OCR wrapper with a resumable per-page JSON cache."""
from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent


def ensure_ocr_binary(cache_dir: Path) -> Path:
    """Compile the Swift Vision helper once and reuse it."""
    src = PACKAGE_DIR / "vision_ocr.swift"
    binary = cache_dir / "bin" / "vision_ocr"
    if binary.exists() and binary.stat().st_mtime >= src.stat().st_mtime:
        return binary
    binary.parent.mkdir(parents=True, exist_ok=True)
    module_cache = cache_dir / "swift-module-cache"
    module_cache.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, CLANG_MODULE_CACHE_PATH=str(module_cache))
    subprocess.run(
        ["swiftc", "-O", "-module-cache-path", str(module_cache), str(src), "-o", str(binary)],
        check=True,
        env=env,
    )
    return binary


def ocr_chunk(images: list[Path], cache_dir: Path, ocr_bin: Path, languages: str) -> int:
    proc = subprocess.run(
        [str(ocr_bin), "--languages", languages],
        input="\n".join(str(p) for p in images) + "\n",
        text=True,
        capture_output=True,
        check=True,
    )
    done = 0
    for raw in proc.stdout.splitlines():
        data = json.loads(raw)
        if "error" in data:
            raise RuntimeError(f"OCR failed for {data['path']}: {data['error']}")
        target = cache_dir / (Path(data["path"]).stem + ".json")
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(target)
        done += 1
    return done


def ocr_book(
    images: list[Path],
    work: Path,
    jobs: int,
    ocr_bin: Path,
    languages: str = "zh-Hans,en-US",
    log: Callable[[str], None] = print,
) -> list[dict]:
    cache_dir = work / "ocr"
    cache_dir.mkdir(parents=True, exist_ok=True)
    todo = [p for p in images if not (cache_dir / f"{p.stem}.json").exists()]
    if todo:
        chunks = [todo[i: i + 12] for i in range(0, len(todo), 12)]
        finished = 0
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = [pool.submit(ocr_chunk, c, cache_dir, ocr_bin, languages) for c in chunks]
            for fut in as_completed(futures):
                finished += fut.result()
                if finished % 60 < 12 or finished == len(todo):
                    log(f"  OCR {finished}/{len(todo)}")
    return [json.loads((cache_dir / f"{p.stem}.json").read_text(encoding="utf-8")) for p in images]
