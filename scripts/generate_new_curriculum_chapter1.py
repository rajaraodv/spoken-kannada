#!/usr/bin/env python3
"""Generate the new kid-curriculum Chapter 1 assets.

This updates:
- data/improved_kids_conversation_curriculum.json with Sarvam Kannada + roman
- data/sarvam_corrections_all_chapters.json for the static chapter renderer
- public/audio/chapter-01/*.wav with cached Sarvam TTS audio
- public/images/gemini-chapter-visuals/chapter-01-new/*.jpg with Gemini Lite images
- data/chapter_visuals.json chapter 1 entries
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


CURRICULUM_PATH = Path("data/improved_kids_conversation_curriculum.json")
CORRECTIONS_PATH = Path("data/sarvam_corrections_all_chapters.json")
VISUALS_PATH = Path("data/chapter_visuals.json")
ENV_PATH = Path(".env.local")
IMAGE_DIR = Path("public/images/gemini-chapter-visuals/chapter-01-new")
AUDIO_DIR = Path("public/audio/chapter-01")
FORCE_ASSET_REGEN = os.environ.get("FORCE_ASSET_REGEN") == "1"

SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
GEMINI_MODEL = "gemini-3.1-flash-lite-image"
GEMINI_INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_-]{20,}")

KANNADA_FONT = "/System/Library/Fonts/Supplemental/NotoSansKannada.ttc"
LATIN_FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

TRANSLATION_MODE = "classic-colloquial"
MANUAL_TRANSLATION_OVERRIDES = {
    "Hello.": ("ಹೆಲೋ.", "Hello."),
    "See you at school tomorrow?": ("ನಾಳೆ ಸ್ಕೂಲ್‌ನಲ್ಲಿ ಸಿಗೋಣವಾ?", "Naale schoolnalli sigonava?"),
    "Bye, Raju.": ("ಬೈ, ರಾಜು.", "Bye, Raju."),
    "Bye, Meena.": ("ಬೈ, ಮೀನಾ.", "Bye, Meena."),
}


def load_dotenv() -> None:
    if not ENV_PATH.exists():
        return
    for raw in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def find_google_key() -> str | None:
    for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_GENAI_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    for root in [Path("/Users/rajaraodv/demos/video-avatars-agent"), Path("/Users/rajaraodv/demos")]:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if any(part in {".git", ".next", "node_modules", "dist", "build", ".venv"} for part in path.parts):
                continue
            if not path.is_file() or path.stat().st_size > 2_000_000:
                continue
            if not (path.name.startswith(".env") or path.suffix in {".py", ".js", ".ts", ".tsx", ".md", ".txt"}):
                continue
            try:
                match = KEY_PATTERN.search(path.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
            if match:
                return match.group(0)
    return None


def request_json(url: str, payload: dict, headers: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", errors="replace")
            if err.code in {429, 500, 502, 503, 504} and attempt < 5:
                time.sleep(8 + attempt * 10)
                continue
            raise RuntimeError(f"HTTP {err.code}: {detail}") from err
        except (TimeoutError, urllib.error.URLError):
            if attempt == 5:
                raise
            time.sleep(4 + attempt * 4)
    raise RuntimeError("Request failed")


def sarvam_translate(text: str, output_script: str, api_key: str) -> str:
    payload = {
        "input": text,
        "source_language_code": "en-IN",
        "target_language_code": "kn-IN",
        "speaker_gender": "Female",
        "mode": TRANSLATION_MODE,
        "model": "mayura:v1",
        "output_script": output_script,
        "enable_preprocessing": True,
    }
    body = request_json(
        SARVAM_TRANSLATE_URL,
        payload,
        {"api-subscription-key": api_key, "Content-Type": "application/json"},
    )
    return str(body["translated_text"]).strip()


def tts(text: str, language_code: str, speaker: str, api_key: str) -> bytes:
    payload = {
        "text": text,
        "target_language_code": language_code,
        "speaker": speaker,
        "model": "bulbul:v3",
        "pace": 0.9,
        "enable_preprocessing": True,
        "speech_sample_rate": 22050,
    }
    body = request_json(
        SARVAM_TTS_URL,
        payload,
        {"api-subscription-key": api_key, "Content-Type": "application/json"},
    )
    audio_base64 = body.get("audios", [None])[0] or body.get("audio") or body.get("audio_base64")
    if not audio_base64:
        raise RuntimeError(f"No audio returned for {text!r}")
    return base64.b64decode(audio_base64)


def correction_key(conversation_id: str, row: int) -> str:
    return f"chapter-01:conversation-{conversation_id}:row-{row:02d}"


def image_slug(conversation_id: str, row: int) -> str:
    return f"conversation-{conversation_id.lower()}-{row:02d}"


def iter_chapter_one_lines(chapter: dict):
    for conv in chapter["conversations"]:
        excerpt = " ".join(f"{line['speaker']}: {line['english']}" for line in conv["lines"])
        for row_index, line in enumerate(conv["lines"], 1):
            yield conv, row_index, line, excerpt


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
    if isinstance(value, list):
        for child in value:
            found = find_image_data(child)
            if found:
                return found
    return None


def generate_image(api_key: str, prompt: str, references: list[Path]) -> bytes:
    input_items: list[dict[str, str]] = [{"type": "text", "text": prompt}]
    for ref in references[:2]:
        input_items.append(
            {
                "type": "image",
                "data": base64.b64encode(ref.read_bytes()).decode("utf-8"),
                "mime_type": "image/jpeg",
            }
        )
    payload = {
        "model": GEMINI_MODEL,
        "input": input_items,
        "response_format": {
            "type": "image",
            "mime_type": "image/jpeg",
            "aspect_ratio": "16:9",
        },
    }
    body = request_json(
        GEMINI_INTERACTIONS_URL,
        payload,
        {"x-goog-api-key": api_key, "Content-Type": "application/json"},
        timeout=180,
    )
    image_data = find_image_data(body)
    if not image_data:
        raise RuntimeError(f"Gemini response did not include image data. Keys: {sorted(body.keys())}")
    return base64.b64decode(image_data)


def conversation_profiles(conv_id: str) -> str:
    if conv_id == "1A":
        return (
            "Raju: Indian school-age boy, blue school shirt, curious and friendly. "
            "Meena: Indian school-age girl, purple kurta or school outfit, warm smile, distinct hairstyle with braid. "
            "Shopkeeper: adult behind the ice cream counter, only background role."
        )
    if conv_id == "1B":
        return (
            "Raju: same Indian school-age boy from conversation 1A, blue school shirt, excited about mango flavor. "
            "Meena: same Indian school-age girl from conversation 1A, purple outfit, excited about chocolate flavor. "
            "Shopkeeper: adult behind the ice cream counter, only background role."
        )
    return (
        "Raju: same Indian school-age boy from earlier in the chapter, blue school shirt, holding mango ice cream or school bag. "
        "Meena: same Indian school-age girl from earlier in the chapter, purple outfit, holding chocolate ice cream or school bag."
    )


def listener_for(conv: dict, row_index: int, line: dict) -> str:
    speakers = [candidate["speaker"] for candidate in conv["lines"]]
    for candidate in speakers[row_index:]:
        if candidate != line["speaker"]:
            return candidate
    for candidate in reversed(speakers[: row_index - 1]):
        if candidate != line["speaker"]:
            return candidate
    return "the other child"


def prompt_for(chapter: dict, conv: dict, row_index: int, line: dict, excerpt: str, previous_reference: bool) -> str:
    listener = listener_for(conv, row_index, line)
    if conv["id"] == "1A":
        setting = "near the entrance of a colorful Indian ice cream shop after school"
        props = "shop doorway, ice cream counter visible in background, school bags, no readable signs"
    elif conv["id"] == "1B":
        setting = "inside the same colorful Indian ice cream shop"
        props = "ice cream counter, mango flavor scoop, chocolate flavor scoop, small table, school bags, no readable signs"
    else:
        setting = "outside the same ice cream shop near school bags and a sunny sidewalk"
        props = "finished ice cream cups, shop doorway, school bags, sunny sidewalk, no readable signs"
    bubble_x = "left" if (conv["id"] == "1A" and line["speaker"] == "Raju") or (conv["id"] in {"1B", "1C"} and line["speaker"] == "Meena") else "right"
    reference = (
        "Use the attached previous image as visual reference. Keep the same characters, faces, clothing, color palette, shop layout, lighting, and storybook style, but update gaze and gestures for the current line."
        if previous_reference
        else "This is the first image for this conversation. Establish the characters, setting, clothing, and warm storybook style clearly."
    )
    return f"""Create one image for a spoken Kannada learning card.

Purpose:
This image teaches kids and English speakers one moment from a spoken Kannada conversation. It must show one person speaking to another person. The app will add the exact speech bubble text later.

Chapter:
Chapter 1: {chapter['title']}

Conversation id:
{conv['id']}

Conversation summary:
{conv['title']}. {conv['goal']}

Full conversation excerpt:
{excerpt}

Current line:
{row_index}

Speaker:
{line['speaker']}

Listener:
{listener}

What is happening in this exact image:
{line['speaker']} is saying this sentence to {listener}: "{line['english']}"

English sentence for context only, do not render:
{line['english']}

Kannada sentence for context only, do not render:
{line['kannada']}

Romanized Kannada for context only, do not render:
{line['roman']}

Scene location:
{setting}

Scene details and props:
{props}

Character profiles and dress code:
{conversation_profiles(conv['id'])}

Visible name badges:
Named people who must be visible and unobstructed: Raju and Meena. Do not render any name text yourself; the app will overlay exact badges.

Character continuity:
{reference}

Speech bubble:
Do not draw a speech bubble and do not render any text. Leave clean open space near the top {bubble_x} for an app-added compact speech bubble.

Composition:
Make the speaker/listener relationship immediately clear with eye contact, body direction, and natural gestures. Keep faces, hands, ice cream, and important props unobstructed. Use a simple 16:9 composition.

Style:
Modern colorful children's storybook cartoon, warm Indian setting, expressive characters, polished and kid-friendly.

Negative instructions:
No text, no letters, no captions, no UI, no watermarks, no fake writing, no shop sign text, no speech bubble, no name labels, no blank label boxes."""


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


def draw_badge(draw: ImageDraw.ImageDraw, label: str, xy: tuple[int, int], fill: tuple[int, int, int]) -> None:
    font = ImageFont.truetype(LATIN_FONT, 30)
    bbox = draw.textbbox((0, 0), label, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x, y = xy
    box = (x - width // 2 - 16, y, x + width // 2 + 16, y + height + 16)
    draw.rounded_rectangle((box[0] + 4, box[1] + 5, box[2] + 4, box[3] + 5), radius=18, fill=(0, 0, 0))
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=(255, 255, 255), width=3)
    draw.text((x - width // 2, y + 7), label, font=font, fill=(255, 255, 255))


def overlay_card(base_path: Path, final_path: Path, line: dict, conv_id: str) -> None:
    image = Image.open(base_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    outside_scene = conv_id in {"1B", "1C"}
    english_font = ImageFont.truetype(LATIN_FONT, 26 if outside_scene else 30)
    kannada_font = ImageFont.truetype(KANNADA_FONT, 27 if outside_scene else 31)
    speaker = line["speaker"]
    speaker_is_left = (conv_id == "1A" and speaker == "Raju") or (outside_scene and speaker == "Meena")
    if outside_scene:
        if conv_id == "1C" and speaker == "Raju":
            box = (565, 10, 1248, 138)
            tail = (1010, 286)
        else:
            box = (565, 10, 1248, 138) if speaker_is_left else (40, 10, 590, 138)
            tail = (715, 306) if speaker_is_left else (940, 286)
    else:
        box = (58, 42, 635, 205) if speaker_is_left else (650, 42, 1230, 205)
        tail = (315, 305) if speaker_is_left else (960, 305)
    draw.rounded_rectangle((box[0] + 7, box[1] + 8, box[2] + 7, box[3] + 8), radius=22, fill=(0, 0, 0))
    tail_x = min(max(tail[0], box[0] + 40), box[2] - 40)
    draw.polygon([(tail_x - 24, box[3] - 4), (tail_x + 24, box[3] - 4), tail], fill=(0, 0, 0))
    draw.rounded_rectangle(box, radius=22, fill=(255, 255, 255), outline=(37, 99, 235), width=4)
    draw.polygon([(tail_x - 24, box[3] - 4), (tail_x + 24, box[3] - 4), tail], fill=(255, 255, 255))
    draw.line([(tail_x - 24, box[3] - 4), tail, (tail_x + 24, box[3] - 4)], fill=(37, 99, 235), width=4)
    x = box[0] + 25
    y = box[1] + 18
    max_width = box[2] - box[0] - 50
    for row in wrapped_lines(line["english"], english_font, max_width):
        draw.text((x, y), row, font=english_font, fill=(15, 23, 42))
        y += 31 if outside_scene else 36
    y += 2 if outside_scene else 4
    for row in wrapped_lines(line["kannada"], kannada_font, max_width):
        draw.text((x, y), row, font=kannada_font, fill=(15, 118, 110))
        y += 32 if outside_scene else 38
    if outside_scene:
        draw_badge(draw, "Meena", (455, 630), (190, 24, 93))
        draw_badge(draw, "Raju", (965, 630), (37, 99, 235))
    else:
        draw_badge(draw, "Raju", (280, 630), (37, 99, 235))
        draw_badge(draw, "Meena", (1010, 630), (190, 24, 93))
    final_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(final_path, quality=94)


def main() -> None:
    load_dotenv()
    sarvam_key = os.environ.get("SARVAM_API_KEY", "").strip()
    google_key = find_google_key()
    if not sarvam_key:
        raise SystemExit("SARVAM_API_KEY is not configured.")
    if not google_key:
        raise SystemExit("GOOGLE_API_KEY/GEMINI_API_KEY is not configured.")

    curriculum = json.loads(CURRICULUM_PATH.read_text(encoding="utf-8"))
    chapter = curriculum["chapters"][0]
    corrections = json.loads(CORRECTIONS_PATH.read_text(encoding="utf-8")) if CORRECTIONS_PATH.exists() else {}
    visuals = json.loads(VISUALS_PATH.read_text(encoding="utf-8")) if VISUALS_PATH.exists() else {}
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating Sarvam Kannada, romanization, and cached WAV audio for Chapter 1...")
    for conv, row_index, line, _excerpt in iter_chapter_one_lines(chapter):
        english = line["english"]
        manual = MANUAL_TRANSLATION_OVERRIDES.get(english)
        if manual:
            kannada, roman = manual
        else:
            kannada = sarvam_translate(english, "fully-native", sarvam_key)
            roman = sarvam_translate(english, "roman", sarvam_key)
        line["kannada"] = kannada
        line["roman"] = roman
        line["translation_mode"] = TRANSLATION_MODE if not manual else f"{TRANSLATION_MODE}+manual_spoken_fix"
        key = correction_key(conv["id"], row_index)
        corrections[key] = {
            "chapter": 1,
            "conversation": conv["id"],
            "row": row_index,
            "english": english,
            "original_roman": roman,
            "sarvam_kannada": kannada,
            "sarvam_roman": roman,
            "source": f"sarvam_translate_mayura_v1_{line['translation_mode']}_new_curriculum_chapter_1",
        }
        slug = image_slug(conv["id"], row_index)
        en_audio = AUDIO_DIR / f"{slug}-en.wav"
        kn_audio = AUDIO_DIR / f"{slug}-kn.wav"
        if FORCE_ASSET_REGEN or not en_audio.exists():
            en_audio.write_bytes(tts(english, "en-IN", "shubh", sarvam_key))
            time.sleep(0.2)
        if FORCE_ASSET_REGEN or not kn_audio.exists():
            kn_audio.write_bytes(tts(kannada, "kn-IN", "priya", sarvam_key))
            time.sleep(0.2)
        print(f"  {conv['id']}:{row_index:02d} {roman} / {kannada}")

    CURRICULUM_PATH.write_text(json.dumps(curriculum, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CORRECTIONS_PATH.write_text(json.dumps(corrections, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Generating Chapter 1 images with {GEMINI_MODEL}...")
    items = []
    previous_by_conversation: dict[str, Path] = {}
    for conv, row_index, line, excerpt in iter_chapter_one_lines(chapter):
        slug = image_slug(conv["id"], row_index)
        base_path = IMAGE_DIR / f"{slug}-base.jpg"
        final_path = IMAGE_DIR / f"{slug}.jpg"
        prompt_path = IMAGE_DIR / f"{slug}.prompt.txt"
        references = []
        previous = previous_by_conversation.get(conv["id"])
        if previous and previous.exists():
            references.append(previous)
        prompt = prompt_for(chapter, conv, row_index, line, excerpt, bool(references))
        prompt_path.write_text(prompt, encoding="utf-8")
        if FORCE_ASSET_REGEN or not base_path.exists():
            print(f"  Generating {slug} with {len(references)} reference image(s)...", flush=True)
            base_path.write_bytes(generate_image(google_key, prompt, references))
            time.sleep(0.5)
        overlay_card(base_path, final_path, line, conv["id"])
        previous_by_conversation[conv["id"]] = base_path
        items.append(
            {
                "img": f"images/gemini-chapter-visuals/chapter-01-new/{slug}.jpg",
                "audio_en": f"audio/chapter-01/{slug}-en.wav",
                "audio_kn": f"audio/chapter-01/{slug}-kn.wav",
                "conversation": conv["id"],
                "row": row_index,
                "english": line["english"],
                "roman": line["roman"],
                "theme_label": conv["title"],
            }
        )

    visuals["1"] = {
        "theme_label": chapter["title"],
        "items": items,
    }
    VISUALS_PATH.write_text(json.dumps(visuals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {CURRICULUM_PATH}, {CORRECTIONS_PATH}, {VISUALS_PATH}")


if __name__ == "__main__":
    main()
