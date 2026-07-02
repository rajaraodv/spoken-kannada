#!/usr/bin/env python3
"""Crop the Lesson 1 comic into reusable visual practice snippets."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image


SOURCE = Path("public/images/chapter-1-meeting-people-cartoon.png")
SOURCE_SVG = Path("public/images/chapter-1-meeting-people-cartoon.svg")
OUT_DIR = Path("public/images/chapter-1-snippets")

NAMES = [
    "01-good-morning",
    "02-i-am-raju",
    "03-he-is-mohan",
    "04-who-are-you",
    "05-i-am-shekhar",
    "06-who-is-she",
    "07-she-is-sheela",
    "08-he-is-shankar",
]


def conversation_1_rects() -> list[tuple[int, int, int, int]]:
    """Return the first eight scene panel rectangles, scaled from SVG to PNG."""
    svg = SOURCE_SVG.read_text(encoding="utf-8")
    image = Image.open(SOURCE)
    match = re.search(r'<svg[^>]*width="(?P<w>\d+)"[^>]*', svg)
    if not match:
        raise SystemExit(f"Could not read SVG width from {SOURCE_SVG}")
    scale = image.width / int(match.group("w"))

    rects: list[tuple[float, float, float, float]] = []
    for m in re.finditer(
        r'<rect x="(?P<x>26)" y="(?P<y>[0-9.]+)" rx="16" width="(?P<w>1028)" height="(?P<h>[0-9.]+)"',
        svg,
    ):
        x = float(m.group("x"))
        y = float(m.group("y"))
        w = float(m.group("w"))
        h = float(m.group("h"))
        rects.append((x, y, x + w, y + h))

    if len(rects) < len(NAMES):
        raise SystemExit(f"Expected at least {len(NAMES)} panel rects, found {len(rects)}")

    # Inset by 2 SVG px so adjacent borders and labels never leak into another crop.
    inset = 2
    scaled = []
    for left, top, right, bottom in rects[: len(NAMES)]:
        scaled.append(
            (
                round((left + inset) * scale),
                round((top + inset) * scale),
                round((right - inset) * scale),
                round((bottom - inset) * scale),
            )
        )
    return scaled


def main() -> None:
    image = Image.open(SOURCE)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, (left, top, right, bottom) in zip(NAMES, conversation_1_rects()):
        crop = image.crop((left, top, right, bottom))
        crop.save(OUT_DIR / f"{name}.png")
    print(f"Wrote {len(NAMES)} snippets to {OUT_DIR}")


if __name__ == "__main__":
    main()
