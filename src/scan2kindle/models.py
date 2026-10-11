"""Small data structures shared by the conversion pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Line:
    text: str
    conf: float
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def h(self) -> float:
        return self.y1 - self.y0

    @property
    def w(self) -> float:
        return self.x1 - self.x0


@dataclass
class Block:
    kind: str  # p, h, img
    text: str = ""
    src: str = ""
    page: int = 0
    continues: bool = False
    confs: list[float] = field(default_factory=list)


@dataclass
class Article:
    page: int
    title: str
    author: str = ""
    start: int = 0
