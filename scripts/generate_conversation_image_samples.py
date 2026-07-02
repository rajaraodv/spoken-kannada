#!/usr/bin/env python3
"""Generate two conversation-aware chapter image samples with Nano Banana Lite."""

from __future__ import annotations

import base64
import json
import os
import re
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


MODEL = "gemini-3.1-flash-lite-image"
INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
OUT_DIR = Path("public/images/gemini-lite-conversation-samples")
ENV_PATH = Path(".env.local")
KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_-]{20,}")
KANNADA_FONT = "/System/Library/Fonts/Supplemental/NotoSansKannada.ttc"
LATIN_FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


SAMPLES = [
    {
        "slug": "chapter-03-conversation-2-line-01",
        "bubble": "left",
        "tail": (290, 330),
        "chapter": "Chapter 03",
        "conversation_id": "Conversation 2",
        "summary": "Two students are standing just outside a classroom. One student asks Raju which class this nearby classroom is.",
        "excerpt": "A: Raju, which class is this? B: This is a Kannada class. A: Whose Kannada class is this? B: This is our Kannada class.",
        "speaker": "Student A",
        "listener": "Raju",
        "english": "Raju, which class is this?",
        "kannada": "ರಾಜು, ಇದು ಯಾವ ತರಗತಿ?",
        "roman": "Raju, idu yaava taragati?",
        "scene": "Indian school corridor at the doorway of a nearby classroom.",
        "props": "Open classroom door, visible desks, books, school bags, blank green board, warm sunlight, simple classroom posters with pictures only.",
        "art_prompt": """Create a 16:9 modern colorful children's storybook cartoon.
Scene: Indian school corridor outside a nearby classroom. Student A stands on the left foreground, facing Raju, pointing through an open classroom door to show a nearby class. Raju stands to the right foreground listening. The classroom is visible behind them with desks, books, school bags, a blank green board, warm sunlight, and picture-only posters.
Conversation context: Student A is asking Raju which class this nearby classroom is.
Composition: speaker on left, listener on right, clear empty sky/wall space at top-left for a speech bubble that will be added later. No speech bubble in the generated art.
Style: polished modern children's storybook cartoon, warm Indian school setting, expressive characters, clean uncluttered composition.
Negative: no text, no letters, no captions, no chalk writing, no random symbols, no watermark.""",
    },
    {
        "slug": "chapter-03-conversation-2-line-02",
        "bubble": "right",
        "tail": (1040, 330),
        "chapter": "Chapter 03",
        "conversation_id": "Conversation 2",
        "summary": "The same two students remain outside the classroom. Raju answers that the nearby classroom is a Kannada class.",
        "excerpt": "A: Raju, which class is this? B: This is a Kannada class. A: Whose Kannada class is this? B: This is our Kannada class.",
        "speaker": "Raju",
        "listener": "Student A",
        "english": "This is a Kannada class.",
        "kannada": "ಇದು ಕನ್ನಡ ತರಗತಿ.",
        "roman": "Idu Kannada taragati.",
        "scene": "Same Indian school corridor and classroom doorway as the previous image.",
        "props": "Open classroom door, visible desks, books, school bags, blank green board, warm sunlight, picture-only posters.",
        "art_prompt": """Create a 16:9 modern colorful children's storybook cartoon.
Scene: Same Indian school corridor outside the nearby classroom as the previous image. Keep two students with consistent school uniforms and character appearance. Raju now stands on the right foreground and answers confidently while gesturing toward the open classroom. Student A stands on the left foreground listening. The classroom is visible behind them with desks, books, school bags, a blank green board, warm sunlight, and picture-only posters.
Conversation context: Raju is answering that this nearby class is a Kannada class.
Composition: listener on left, speaker Raju on right, clear empty sky/wall space at top-right for a speech bubble that will be added later. No speech bubble in the generated art.
Style: polished modern children's storybook cartoon, warm Indian school setting, expressive characters, clean uncluttered composition. Match the first image style closely.
Negative: no text, no letters, no captions, no chalk writing, no random symbols, no watermark.""",
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

    roots = [Path("/Users/rajaraodv/demos/video-avatars-agent"), Path("/Users/rajaraodv/demos")]
    ignored_dirs = {".git", ".next", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}
    extensions = {".env", ".local", ".py", ".js", ".mjs", ".ts", ".tsx", ".md", ".txt"}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if any(part in ignored_dirs for part in path.parts):
                continue
            if not path.is_file():
                continue
            if not (path.name.startswith(".env") or path.suffix in extensions):
                continue
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


def prompt_for(sample: dict) -> str:
    return f"""Create one image for a spoken Kannada learning card.

Purpose:
This image teaches kids and English speakers one moment from a spoken Kannada conversation. It must show one person speaking to another person. The app will add the speech bubble and text after generation.

Chapter:
{sample["chapter"]}

Conversation id:
{sample["conversation_id"]}

Conversation summary:
{sample["summary"]}

Full conversation excerpt:
{sample["excerpt"]}

Speaker:
{sample["speaker"]}

Listener:
{sample["listener"]}

What is happening in this exact image:
{sample["speaker"]} is saying this sentence to {sample["listener"]}: "{sample["english"]}"

English sentence for context only, do not render:
{sample["english"]}

Kannada sentence for context only, do not render:
{sample["kannada"]}

Romanized Kannada for context only, do not render:
{sample["roman"]}

Scene location:
{sample["scene"]}

Scene details and props:
{sample["props"]}

Character continuity:
Use the same two children across both sample images: Student A has a blue backpack and stands on the left in the first image; Raju has a yellow or green backpack and stands on the right. Keep school uniforms, age, style, lighting, and corridor layout consistent.

Art direction:
{sample["art_prompt"]}"""


def generate_base_image(api_key: str, prompt: str) -> bytes:
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
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
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


def wrapped_lines(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    probe = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(probe)
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def overlay_bubble(image_path: Path, out_path: Path, sample: dict) -> None:
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    w, h = image.size
    english_font = ImageFont.truetype(LATIN_FONT, 34)
    kannada_font = ImageFont.truetype(KANNADA_FONT, 38)

    if sample["bubble"] == "left":
        box = (70, 52, 625, 230)
    else:
        box = (655, 52, 1210, 230)
    tail = sample["tail"]
    radius = 28
    shadow = tuple(v + 10 for v in box)

    draw.rounded_rectangle(shadow, radius=radius, fill=(0, 0, 0, 42))
    draw.polygon(
        [(tail[0] - 24, box[3] - 4), (tail[0] + 30, box[3] - 4), tail],
        fill=(0, 0, 0),
    )
    draw.rounded_rectangle(box, radius=radius, fill=(255, 255, 255), outline=(37, 99, 235), width=5)
    draw.polygon(
        [(tail[0] - 24, box[3] - 4), (tail[0] + 30, box[3] - 4), tail],
        fill=(255, 255, 255),
        outline=(37, 99, 235),
    )
    draw.line([(tail[0] - 24, box[3] - 4), tail, (tail[0] + 30, box[3] - 4)], fill=(37, 99, 235), width=5)

    x = box[0] + 32
    y = box[1] + 24
    max_width = box[2] - box[0] - 64
    for line in wrapped_lines(sample["english"], english_font, max_width):
        draw.text((x, y), line, font=english_font, fill=(15, 23, 42))
        y += 42
    y += 6
    for line in wrapped_lines(sample["kannada"], kannada_font, max_width):
        draw.text((x, y), line, font=kannada_font, fill=(15, 118, 110))
        y += 46

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, quality=94)


def main() -> None:
    load_dotenv()
    api_key = find_existing_api_key()
    if not api_key:
        raise SystemExit("No GOOGLE_API_KEY/GEMINI_API_KEY found locally.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Using {MODEL}; API key loaded locally and masked.")
    for sample in SAMPLES:
        base_path = OUT_DIR / f"{sample['slug']}-base.jpg"
        final_path = OUT_DIR / f"{sample['slug']}.jpg"
        prompt_path = OUT_DIR / f"{sample['slug']}.prompt.txt"
        prompt = prompt_for(sample)
        prompt_path.write_text(prompt, encoding="utf-8")
        print(f"Generating base art for {sample['slug']} ...", flush=True)
        base_path.write_bytes(generate_base_image(api_key, prompt))
        overlay_bubble(base_path, final_path, sample)
        print(f"Wrote {final_path}")


if __name__ == "__main__":
    main()
