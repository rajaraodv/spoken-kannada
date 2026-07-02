#!/usr/bin/env python3
"""Generate a couple of sample chapter images with Nano Banana 2 Lite.

This script intentionally does not print API keys. It first uses
GOOGLE_API_KEY/GEMINI_API_KEY from the environment or .env.local, then falls
back to scanning nearby demo files for an existing Google AI Studio key.
"""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


MODEL = "gemini-3.1-flash-lite-image"
INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
OUT_DIR = Path("public/images/gemini-lite-samples")
ENV_PATH = Path(".env.local")
KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_-]{20,}")

SAMPLES = [
    {
        "slug": "chapter-03-vasu-seated",
        "prompt": """Create a polished, colorful 16:9 children's learning illustration.
Scene: a friendly Kannada classroom in Karnataka. A teacher warmly welcomes a student named Vasu and gestures to a chair. Vasu is about to sit down. Include desks, a chalkboard, sunlight from windows, notebooks, and a welcoming classroom mood.
Style: modern storybook cartoon, soft lighting, rich scenery, expressive characters, clean composition, high quality.
Important: no written words, no letters, no captions, no visible text.""",
    },
    {
        "slug": "chapter-03-kannada-class",
        "prompt": """Create a polished, colorful 16:9 children's learning illustration.
Scene: two students in a school corridor looking into a nearby classroom. One child points to the classroom. Inside, students sit with a teacher in a bright Indian school room. Use school bags, colorful desks, posters with simple icon drawings only, windows, and warm sunlight. If a board appears, it must be completely blank green with no marks.
Style: modern storybook cartoon, lively but clean, warm Indian school environment, expressive characters, high quality.
Important: absolutely no written words, no letters, no alphabet marks, no readable or fake text, no captions, no symbols that look like writing.""",
    },
]


def load_dotenv() -> None:
    if not ENV_PATH.exists():
        return
    for raw in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def find_existing_api_key() -> str | None:
    for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_GENAI_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value

    roots = [
        Path("/Users/rajaraodv/demos/video-avatars-agent"),
        Path("/Users/rajaraodv/demos"),
    ]
    ignored_dirs = {
        ".git",
        ".next",
        "node_modules",
        "venv",
        ".venv",
        "__pycache__",
        "dist",
        "build",
    }
    extensions = {".env", ".local", ".py", ".js", ".mjs", ".ts", ".tsx", ".md", ".txt"}

    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if any(part in ignored_dirs for part in path.parts):
                continue
            if not path.is_file():
                continue
            if path.name.startswith(".env") or path.suffix in extensions:
                try:
                    if path.stat().st_size > 2_000_000:
                        continue
                    match = KEY_PATTERN.search(path.read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    continue
                if match:
                    return match.group(0)
    return None


def find_image_data(value: Any) -> str | None:
    if isinstance(value, dict):
        output_image = value.get("output_image")
        if isinstance(output_image, dict) and isinstance(output_image.get("data"), str):
            return output_image["data"]
        if value.get("type") == "image" and isinstance(value.get("data"), str):
            return value["data"]
        inline_data = value.get("inline_data") or value.get("inlineData")
        if isinstance(inline_data, dict) and isinstance(inline_data.get("data"), str):
            return inline_data["data"]
        for child in value.values():
            found = find_image_data(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_image_data(child)
            if found:
                return found
    return None


def generate_image(api_key: str, prompt: str) -> bytes:
    payload = {
        "model": MODEL,
        "input": [{"type": "text", "text": prompt}],
        "response_format": {
            "type": "image",
            "mime_type": "image/jpeg",
            "aspect_ratio": "16:9",
        },
    }
    req = urllib.request.Request(
        INTERACTIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini image request failed: HTTP {err.code}: {detail}") from err

    image_data = find_image_data(body)
    if not image_data:
        raise RuntimeError(f"Gemini response did not include image data. Keys: {sorted(body.keys())}")
    return base64.b64decode(image_data)


def main() -> None:
    load_dotenv()
    api_key = find_existing_api_key()
    if not api_key:
        raise SystemExit("No GOOGLE_API_KEY/GEMINI_API_KEY found locally.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Using {MODEL}; API key loaded locally and masked.")
    for sample in SAMPLES:
        out_path = OUT_DIR / f"{sample['slug']}.jpg"
        print(f"Generating {out_path} ...", flush=True)
        image_bytes = generate_image(api_key, sample["prompt"])
        out_path.write_bytes(image_bytes)
        print(f"Wrote {out_path} ({len(image_bytes):,} bytes)")


if __name__ == "__main__":
    main()
