#!/usr/bin/env python3
"""Generate all Chapter 1 conversation images with Gemini Flash Lite Image."""

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

from build_page_by_page_html import (
    correction_for,
    load_sarvam_corrections,
    with_original_deictic,
)


MODEL = "gemini-3.1-flash-lite-image"
INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
DATA_PATH = Path("data/page_by_page_conversations.json")
VISUALS_PATH = Path("data/chapter_visuals.json")
OUT_DIR = Path("public/images/gemini-chapter-visuals/chapter-01")
ENV_PATH = Path(".env.local")
KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_-]{20,}")
KANNADA_FONT = "/System/Library/Fonts/Supplemental/NotoSansKannada.ttc"
LATIN_FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


CONVERSATION_SUMMARIES = {
    "1": "Raju greets Shekhar, introduces nearby Mohan, asks who Shekhar is, asks about Sheela who is farther away, and then introduces nearby Shankar.",
    "2": "Raju introduces himself, says he is a Kannada teacher, introduces his friend Mohan, asks Shekhar's name and profession, then asks about Lalitha and whether she is a doctor.",
    "3": "An adult asks a child named Kiran his name and whether the man nearby is his father.",
    "Continuation": "The adult continues asking Kiran about a woman and his younger sister Manju.",
}

SCENE_BY_CONVERSATION = {
    "1": "A bright school courtyard or classroom doorway in Karnataka where children are greeting and introducing friends.",
    "2": "A warm Kannada classroom with a teacher, students, books, desk, blank board, and school bags.",
    "3": "A friendly home entrance or school visiting area where an adult speaks kindly with a child and family members are visible.",
    "Continuation": "The same friendly home entrance or school visiting area with Kiran, his family, and his younger sister Manju.",
}

CHARACTER_CONTINUITY = """Use a consistent modern children's storybook cartoon style for all Chapter 1 images.
Raju: Indian boy or young male teacher depending on conversation; slim, side-parted black hair, expressive eyebrows, blue shirt. In conversation 2 he is an adult teacher with a book or folder.
Shekhar: Indian boy/young man with rounder face, short wavy black hair, green shirt or backpack when learning. When he says he is a doctor, make him an adult doctor in a white coat with stethoscope.
Mohan: Indian boy with darker tan/orange shirt, slightly taller than Raju and Shekhar, wavy hair, calm expression; visually distinct from Shekhar.
Sheela: Indian girl with long tied-back hair or braid, pink/purple outfit, smaller/farther away when the sentence uses 'that person/she'.
Shankar: Indian boy with maroon/purple shirt, shorter hair, different face shape from Mohan and Shekhar, nearby when introduced with 'this person'.
Lalita: Indian adult woman, sari or salwar when discussed from a distance; nurse uniform/medical cue when the sentence says she is a nurse.
Kiran: young Indian child, short, yellow shirt, round childlike face, visibly younger than adults.
Father: adult Indian man, taller than Kiran, moustache or mature face, plain shirt and trousers.
Teacher: adult Indian woman, sari, clearly older than Kiran.
Manju: young Indian girl, smaller than Kiran, dress or school frock, childlike face.
Keep faces, clothing colors, room/courtyard layout, lighting, and style consistent across adjacent images."""

BADGE_COLORS = {
    "Raju": (37, 99, 235),
    "Shekhar": (22, 163, 74),
    "Mohan": (217, 119, 6),
    "Sheela": (219, 39, 119),
    "Shankar": (124, 58, 237),
    "Lalita": (190, 24, 93),
    "Kiran": (245, 158, 11),
    "Teacher": (15, 118, 110),
    "Father": (71, 85, 105),
    "Manju": (147, 51, 234),
}

BADGE_POSITIONS = {
    "left": (205, 620),
    "far_left": (185, 520),
    "mid_left": (475, 620),
    "center": (650, 620),
    "mid_right": (890, 620),
    "right": (1095, 620),
    "far_right": (1135, 500),
    "far_center": (705, 500),
    "conv2_raju": (215, 620),
    "conv2_mohan": (520, 620),
    "conv2_lalita": (805, 520),
    "conv2_shekhar": (1110, 620),
    "family_teacher": (210, 620),
    "family_kiran": (640, 620),
    "family_father": (1110, 520),
    "family_manju": (1000, 620),
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


def chapter_one_rows() -> list[dict]:
    conversations = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    corrections = load_sarvam_corrections()
    rows: list[dict] = []
    current_chapter: int | None = None
    assigned: list[tuple[int, dict]] = []
    for conv in conversations:
        if conv.get("lesson") is not None:
            current_chapter = int(conv["lesson"])
        if current_chapter is not None:
            assigned.append((current_chapter, conv))
    for chapter, conv in assigned:
        if chapter != 1:
            continue
        conv_id = str(conv["number"])
        full_excerpt = " ".join(
            f'{row.get("speaker", "")}: {row.get("english", "")}' for row in conv.get("rows", [])
        )
        for row_index, row in enumerate(conv.get("rows", []), 1):
            original_roman = str(row.get("roman") or "")
            correction = with_original_deictic(correction_for(corrections, 1, conv_id, row_index), original_roman)
            english = str((correction or {}).get("english") or row.get("english") or "").strip()
            kannada = str((correction or {}).get("sarvam_kannada") or "").strip()
            roman = str((correction or {}).get("sarvam_roman") or original_roman).strip()
            if not english:
                continue
            rows.append(
                {
                    "chapter": 1,
                    "conversation": conv_id,
                    "row": row_index,
                    "speaker": str(row.get("speaker") or ""),
                    "english": english,
                    "kannada": kannada,
                    "roman": roman,
                    "original_roman": original_roman,
                    "full_excerpt": full_excerpt,
                    "theme_label": "Introductions and people",
                }
            )
    return rows


def speaker_listener(row: dict) -> tuple[str, str, str]:
    conv = row["conversation"]
    speaker = row["speaker"]
    english = row["english"].lower()
    if conv == "1":
        if speaker == "A":
            if "mohan" in english:
                return "Raju", "Shekhar", "Raju is pointing to nearby Mohan while speaking to Shekhar."
            if "she" in english:
                return "Raju", "Shekhar", "Raju is asking Shekhar about Sheela, who is farther away across the scene."
            return "Raju", "Shekhar", "Raju is speaking to Shekhar."
        if "sheela" in english:
            return "Shekhar", "Raju", "Shekhar answers Raju while indicating Sheela farther away."
        if "shankar" in english:
            return "Shekhar", "Raju", "Shekhar introduces nearby Shankar to Raju."
        return "Shekhar", "Raju", "Shekhar is replying to Raju."
    if conv == "2":
        if speaker == "A":
            return "Raju", "Shekhar", "Raju, a Kannada teacher, is speaking to Shekhar in the classroom."
        return "Shekhar", "Raju", "Shekhar is answering Raju in the classroom."
    if conv in {"3", "Continuation"}:
        if speaker == "A":
            return "Adult teacher", "Kiran", "The adult is asking Kiran a kind question."
        return "Kiran", "Adult teacher", "Kiran is answering the adult and referring to his family."
    return f"Speaker {speaker}", "the other person", "One person is speaking to the other."


def is_family_target(row: dict) -> bool:
    return (str(row["conversation"]) == "3" and int(row["row"]) == 4) or str(row["conversation"]) == "Continuation"


def visible_characters(row: dict) -> list[tuple[str, str]]:
    english = row["english"].lower()
    conv = str(row["conversation"])
    mentions_she = bool(re.search(r"\bshe\b|\bher\b", english))
    if is_family_target(row):
        characters = [("Teacher", "family_teacher"), ("Kiran", "family_kiran")]
        if str(row["conversation"]) == "3" and "father" in english:
            characters.append(("Father", "family_father"))
        if str(row["conversation"]) == "Continuation":
            characters.extend([("Manju", "family_manju"), ("Father", "family_father")])
        return characters
    if conv == "1":
        if mentions_she or "sheela" in english:
            return [("Sheela", "far_left"), ("Raju", "mid_right"), ("Shekhar", "right")]
        if "shankar" in english:
            return [("Raju", "left"), ("Shankar", "center"), ("Shekhar", "right")]
        if "mohan" in english:
            return [("Raju", "left"), ("Mohan", "center"), ("Shekhar", "right")]
        return [("Raju", "left"), ("Mohan", "center"), ("Shekhar", "right")]
    if conv == "2":
        return [
            ("Raju", "conv2_raju"),
            ("Mohan", "conv2_mohan"),
            ("Lalita", "conv2_lalita"),
            ("Shekhar", "conv2_shekhar"),
        ]
    if conv == "3":
        if "father" in english:
            return [("Teacher", "left"), ("Kiran", "center"), ("Father", "right")]
        return [("Teacher", "left"), ("Kiran", "center")]
    if conv == "Continuation":
        if "manju" in english or "sister" in english:
            return [("Teacher", "left"), ("Kiran", "center"), ("Manju", "far_center")]
        if "saroja" in english or "she" in english:
            return [("Teacher", "left"), ("Kiran", "center"), ("Manju", "far_center")]
        return [("Teacher", "left"), ("Kiran", "center")]
    return []


def character_profiles(row: dict) -> str:
    english = row["english"].lower()
    conv = str(row["conversation"])
    profiles = []
    for name, _ in visible_characters(row):
        if name == "Raju":
            role = "Kannada teacher in conversation 2" if conv == "2" else "school-age boy"
            dress = "adult Kannada teacher, neat blue shirt, holding a book or folder" if conv == "2" else "blue school shirt and dark shorts"
        elif name == "Shekhar":
            role = "adult doctor" if conv == "2" else ("doctor" if "doctor" in english else "learner/friend")
            dress = "adult male doctor in white coat with stethoscope" if conv == "2" or "doctor" in english else "green backpack or green accents"
        elif name == "Mohan":
            role = "nearby friend"
            dress = "warm orange or tan shirt so he is distinct from Raju and Shekhar"
        elif name == "Sheela":
            role = "girl farther away"
            dress = "pink or purple school outfit"
        elif name == "Shankar":
            role = "nearby friend"
            dress = "purple or maroon shirt, distinct from Mohan"
        elif name == "Lalita":
            role = "adult nurse" if conv == "2" else ("nurse" if "nurse" in english else "woman being discussed")
            dress = "adult woman nurse in a clean nurse uniform with medical cue" if conv == "2" or "nurse" in english else "simple sari or salwar, farther away"
        elif name == "Kiran":
            role = "younger child"
            dress = "yellow child shirt, shorter than the adults"
        elif name == "Teacher":
            role = "adult teacher"
            dress = "adult sari or neat teacher outfit"
        elif name == "Father":
            role = "Kiran's father"
            dress = "adult shirt and trousers, older than Kiran"
        elif name == "Manju":
            role = "younger sister"
            dress = "younger girl's dress, visibly smaller than Kiran"
        else:
            role = "conversation participant"
            dress = "clear distinct clothing"
        profiles.append(f"{name}: {role}; dress code: {dress}.")
    return " ".join(profiles)


def visible_name_badges(row: dict) -> str:
    badges = [name for name, _ in visible_characters(row)]
    if not badges:
        return "Named people: none."
    return (
        "Named people who must be clearly visible and unobstructed: "
        + ", ".join(badges)
        + ". Do not render any names, labels, blank boxes, white rectangles, or placeholder tags in the image."
    )


def layout_instruction(row: dict) -> str:
    english = row["english"].lower()
    conv = str(row["conversation"])
    if conv == "1":
        if "who is she" in english or "sheela" in english:
            return (
                "Controlled layout: place Sheela alone far on the left/background in pink or purple. "
                "Place Raju and Shekhar together on the right/foreground, with Raju slightly left of Shekhar. "
                "Do not put Raju under or next to the far-left girl."
            )
        if "shankar" in english:
            return (
                "Controlled layout: place Raju on the left foreground, Shankar nearby in the center foreground, "
                "and Shekhar on the right foreground. Keep Shankar distinct from Mohan."
            )
        return (
            "Controlled layout: place Raju on the left foreground, Mohan in the center or center-background, "
            "and Shekhar on the right foreground. Raju and Shekhar should not look like twins."
        )
    if conv == "2":
        if "mohan" in english or "friend" in english:
            return (
                "Controlled layout: place Raju on the left foreground, Mohan in the center/background as the friend being introduced, "
                "and Shekhar on the right foreground. Keep Mohan visually distinct from Shekhar."
            )
        if "lalit" in english or re.search(r"\bshe\b|\bher\b", english) or "nurse" in english:
            return (
                "Controlled layout: place Raju on the left foreground, Shekhar on the right foreground, "
                "and Lalita farther away near the center/background. If the sentence says nurse, make Lalita visibly a nurse."
            )
        if "doctor" in english:
            return (
                "Controlled layout: place Raju on the left foreground and Shekhar on the right foreground as an adult doctor "
                "wearing a white coat and stethoscope."
            )
        return "Controlled layout: place Raju on the left foreground and Shekhar on the right foreground."
    if conv == "3":
        if "father" in english:
            return (
                "Controlled layout: place the adult teacher on the left foreground, Kiran in the center foreground, "
                "and Father far on the right/background as a taller adult man."
            )
        return "Controlled layout: place the adult teacher on the left foreground and young Kiran on the right or center foreground."
    if conv == "Continuation":
        return (
            "Controlled layout: place the adult teacher on the left foreground, Kiran in the center foreground, "
            "and Manju as a younger girl farther left or in the background when she is discussed."
        )
    return "Controlled layout: keep each named person in a distinct, non-overlapping position."


def scene_props(row: dict) -> str:
    text = f"{row['english']} {row['roman']}".lower()
    props = ["warm Indian setting", "simple picture-only posters", "no readable background text"]
    if any(word in text for word in ["name", "who", "father", "sister", "friend"]):
        props.append("clear character staging so the named or referenced person is visible")
    if any(word in text for word in ["teacher", "kannada"]):
        props.extend(["books", "teacher desk", "blank green board", "school bags"])
    if "doctor" in text or "nurse" in text:
        props.extend(["small doctor bag", "stethoscope prop", "nurse visual cue"])
    if any(word in text for word in ["ivaru", "this", "he is mohan", "he is shankar"]):
        props.append("referenced person close to speaker/listener in foreground")
    if any(word in text for word in ["avaru", "she", "her"]):
        props.append("referenced person farther away or across the room")
    return ", ".join(props)


def required_staging(row: dict) -> str:
    english = row["english"].lower()
    conversation = str(row["conversation"])
    if conversation == "1":
        if "mohan" in english:
            return (
                "Required staging: show exactly three schoolchildren. Raju is the speaker on the left, "
                "Shekhar is listening, and Mohan is a distinct third boy standing nearby in the foreground. "
                "Raju must point toward Mohan; do not merge Mohan and Shekhar into one person."
            )
        if "who is she" in english or "sheela" in english:
            return (
                "Required staging: show Raju and Shekhar in the foreground, and Sheela as a distinct girl "
                "farther away across the courtyard or classroom doorway. The distance should visually teach "
                "avaru/that person."
            )
        if "shankar" in english:
            return (
                "Required staging: show Shankar as a distinct nearby boy in the foreground, close to Raju "
                "and Shekhar. The distance should visually teach ivaru/this person."
            )
        return (
            "Required staging: keep Raju, Shekhar, and nearby Mohan available in the scene when possible, "
            "because this is a three-person introduction conversation."
        )
    if any(name in english for name in ["father", "saroj", "manju", "sister"]):
        return "Required staging: the family member being discussed must be visible and easy to identify."
    return "Required staging: make the person or object being discussed visually obvious."


def prompt_for(row: dict, previous_reference: bool) -> str:
    speaker, listener, action = speaker_listener(row)
    ref_text = (
        "A previous Chapter 1 image is attached. Use it as a visual reference for the same characters, faces, clothing, setting, lighting, room/courtyard layout, and style."
        if previous_reference
        else "This is the first image for this continuity group. Establish the character designs and setting clearly."
    )
    return f"""Create one image for a spoken Kannada learning card.

Purpose:
This image teaches kids and English speakers one moment from a spoken Kannada conversation. It must show one person speaking to another person. The app will add the speech bubble and exact English/Kannada text after generation.

Chapter:
Chapter 1

Conversation id:
Conversation {row['conversation']}

Conversation summary:
{CONVERSATION_SUMMARIES.get(row['conversation'], 'People are having a simple spoken Kannada conversation.')}

Full conversation excerpt:
{row['full_excerpt']}

Current line:
{row['row']}

Speaker:
{speaker}

Listener:
{listener}

What is happening in this exact image:
{speaker} is saying this sentence to {listener}: "{row['english']}" {action}

English sentence for context only, do not render:
{row['english']}

Kannada sentence for context only, do not render:
{row['kannada']}

Romanized Kannada for context only, do not render:
{row['roman']}

Scene location:
{SCENE_BY_CONVERSATION.get(row['conversation'], 'A warm Indian school setting.')}

Scene details and props:
{scene_props(row)}

Character profiles and dress code:
{character_profiles(row)}

Visible named people:
{visible_name_badges(row)}

Layout and label safety:
{layout_instruction(row)}

{required_staging(row)}

Character continuity:
{CHARACTER_CONTINUITY}
{ref_text}

Composition:
Show the speaker and listener relationship immediately. Speaker should face, gesture, or point toward the listener or referenced person/object. If this/ivaru is implied, put the referenced person close. If that/avaru is implied, put the referenced person farther away.
Leave clean wall/sky/board-free space near the top for a speech bubble that will be added later. Keep named characters unobstructed. Do not draw a speech bubble, name badge, blank label box, or name-badge text yourself.

Style:
Modern colorful children's storybook cartoon, warm Indian environment, expressive characters, clean readable 16:9 composition.

Negative instructions:
No text, no letters, no captions, no UI, no watermarks, no fake writing, no chalk writing, no random symbols, no generated speech bubble, no generated name labels, no blank white label rectangles."""


def shared_base_prompt_for_conversation(conversation: str, rows: list[dict]) -> str:
    full_excerpt = " ".join(f'{row["speaker"]}: {row["english"]}' for row in rows)
    if conversation == "2":
        return f"""Create one reusable base scene image for a spoken Kannada learning conversation.

Purpose:
This base image will be reused for every sentence card in Conversation 2. The app will add different speech bubbles and exact name badges later. Do not draw any speech bubbles, names, labels, signs, writing, or text.

Chapter:
Chapter 1

Conversation id:
Conversation 2

Conversation summary:
{CONVERSATION_SUMMARIES["2"]}

Full conversation excerpt:
{full_excerpt}

Conversation setting:
A warm Kannada classroom or training room in Karnataka. The conversation stays in this same room for all lines.

Stable cast and exact layout:
Raju: adult Indian male Kannada teacher, slim, side-parted black hair, blue teacher shirt, holding a book or folder. Place him on the left foreground.
Mohan: adult Indian male friend, tan/orange shirt, wavy hair, calm expression. Place him in the center or center-left background, distinct from Shekhar.
Lalita: adult Indian woman nurse, nurse uniform or clear medical cue. Place her farther back near the center-right background, visible but not blocking the main speakers.
Shekhar: adult Indian male doctor, rounder face, short wavy hair, white doctor coat and stethoscope. Place him on the right foreground.

Scene props:
Books, school bags, a blank board with no writing, teacher desk, simple medical bag or stethoscope cue, warm Indian classroom details. No readable background text.

Composition:
Show all four people in one stable wide 16:9 scene. Keep their positions stable and leave clean wall space near the top for the app to overlay speech bubbles. Make each person visually distinct by age, role, face, hair, clothing, and accessories. Do not make the people look like copies of each other.

Style:
Modern colorful children's storybook cartoon, warm Indian environment, expressive characters, clean readable 16:9 composition.

Negative instructions:
No text, no letters, no captions, no UI, no watermarks, no fake writing, no chalk writing, no random symbols, no generated speech bubble, no generated name labels, no blank white label rectangles."""
    if conversation == "family":
        return f"""Create one reusable base scene image for a spoken Kannada learning family conversation.

Purpose:
This base image will anchor cards 27-34 in Chapter 1. The app will add sentence-specific speech bubbles and exact name badges later. Do not draw any speech bubbles, names, labels, signs, writing, or text.

Chapter:
Chapter 1

Conversation id:
Conversation 3 continuation / family introduction

Conversation summary:
Kiran answers the adult teacher that the man is his father. The adult then asks about a girl, incorrectly guessing the name Saroja. Kiran says no, explains she is his younger sister, and says her name is Manju.

Full conversation excerpt:
{full_excerpt}

Conversation setting:
A warm school visiting area or classroom doorway in Karnataka. This is one continuous conversation in one place.

Stable cast and exact layout:
Teacher: adult Indian woman teacher in a sari, kind expression, left foreground. She is the adult asking questions.
Kiran: young Indian boy, short child, yellow shirt, center foreground. He answers the teacher.
Father: adult Indian man, taller than Kiran, mature face or moustache, simple shirt and trousers, right background. He is Kiran's father.
Manju: young Indian girl, visibly younger sister, dress or school frock, right or center-right background but closer than Father. She is the girl being discussed; do not create any separate person named Saroja.

Scene props:
Warm Indian classroom/school doorway, simple picture-only posters, school bag, potted plant, open walking space. No readable background text.

Composition:
Show all four people in one stable wide 16:9 scene. Keep their identities, clothing, and relative positions clear. Teacher and Kiran should be the foreground speakers. Father and Manju should be visible as referenced family members. Make Manju visually distinct from Father and Kiran, and make Father clearly older than Kiran. Leave clean top space for compact app-overlaid speech bubbles.

Style:
Modern colorful children's storybook cartoon, warm Indian environment, expressive characters, clean readable 16:9 composition.

Negative instructions:
No text, no letters, no captions, no UI, no watermarks, no fake writing, no chalk writing, no random symbols, no generated speech bubble, no generated name labels, no blank white label rectangles, no character labeled Saroja."""
    raise ValueError(f"No shared base prompt configured for conversation {conversation}")


def conversation_2_line_action(row: dict) -> str:
    english = row["english"].lower()
    if "my name is raju" in english or "kannada teacher" in english:
        return "Raju is the focus, facing Shekhar and gesturing politely to himself with one hand."
    if "friend" in english or "mohan" in english:
        return "Raju is pointing toward Mohan in the center/background while Shekhar looks at Mohan."
    if "who are you" in english or "what is your name" in english:
        return "Raju is asking Shekhar a question, facing Shekhar and pointing or gesturing toward Shekhar."
    if "i am a doctor" in english or "my name is shekhar" in english:
        return "Shekhar is the focus, facing Raju and gesturing to himself while answering."
    if "lalit" in english or "she" in english or "nurse" in english or "yes" in english:
        if row["speaker"] == "A":
            return "Raju is asking about Lalita, pointing toward Lalita in the background while Shekhar looks where Raju points."
        return "Shekhar is answering while gesturing toward Lalita in the background."
    return "The current speaker is the focus and faces the listener naturally."


def prompt_for_conversation_2_line(row: dict, previous_reference: bool) -> str:
    ref_text = (
        "The shared Conversation 2 base scene is attached, and the previous line image may also be attached. Preserve the same room, character identities, clothing, relative positions, lighting, and cartoon style."
        if previous_reference
        else "The shared Conversation 2 base scene is attached. Preserve the same room, character identities, clothing, relative positions, lighting, and cartoon style."
    )
    speaker, listener, _ = speaker_listener(row)
    return f"""Create one line-specific image for a spoken Kannada learning card.

Purpose:
This image is one sentence from Conversation 2. Use the attached shared base scene as the visual anchor, but update the characters' gaze, pointing, posture, and focus so this specific sentence makes sense. The app will add the speech bubble and exact English/Kannada text after generation.

Chapter:
Chapter 1

Conversation id:
Conversation 2

Conversation summary:
{CONVERSATION_SUMMARIES["2"]}

Full conversation excerpt:
{row['full_excerpt']}

Current line:
{row['row']}

Speaker:
{speaker}

Listener:
{listener}

What is happening in this exact image:
{conversation_2_line_action(row)} The sentence is: "{row['english']}"

English sentence for context only, do not render:
{row['english']}

Kannada sentence for context only, do not render:
{row['kannada']}

Romanized Kannada for context only, do not render:
{row['roman']}

Stable cast:
Raju: adult Indian male Kannada teacher, slim, side-parted black hair, blue teacher shirt, holding a book or folder, left foreground.
Mohan: adult Indian male friend, tan/orange shirt, wavy hair, center/background.
Lalita: adult Indian woman nurse, nurse uniform or clear medical cue, center-right/background.
Shekhar: adult Indian male doctor, rounder face, white doctor coat and stethoscope, right foreground.

Scene continuity:
{ref_text}

Composition:
Keep all four characters recognizable and in roughly the same positions as the base scene. Change only gaze, hand gesture, slight body direction, and focus needed for this sentence. Leave clean top space for a smaller app-overlaid speech bubble. Do not draw speech bubbles, text, name badges, labels, signs, or blank label boxes.

Style:
Modern colorful children's storybook cartoon, warm Indian classroom, expressive characters, clean readable 16:9 composition.

Negative instructions:
No text, no letters, no captions, no UI, no watermarks, no fake writing, no chalk writing, no random symbols, no generated speech bubble, no generated name labels, no blank white label rectangles."""


def family_line_action(row: dict) -> str:
    english = row["english"].lower()
    conv = str(row["conversation"])
    if conv == "3" and "father" in english:
        return "Kiran is answering the teacher and pointing or gesturing toward Father in the right background. Father is clearly the adult man being referenced."
    if "is her name saroja" in english:
        return "Teacher is asking Kiran about Manju, pointing toward Manju in the background. Manju is the girl being discussed; do not show or label anyone as Saroja."
    if english.strip().startswith("no"):
        return "Kiran is answering no to the teacher, using a small no gesture while Manju remains visible in the background."
    if "not saroja" in english:
        return "Kiran is explaining that the girl's name is not Saroja, gesturing toward Manju in the background."
    if "who is she" in english:
        return "Teacher is asking who Manju is, pointing toward Manju while Kiran looks at Manju."
    if "younger sister" in english:
        return "Kiran is answering proudly and pointing toward Manju, showing that she is his younger sister."
    if "what is her name" in english:
        return "Teacher is asking Kiran for Manju's name, looking at Kiran while lightly gesturing toward Manju."
    if "name is manju" in english:
        return "Kiran is answering that the girl is Manju, pointing toward Manju in the background."
    return "The current speaker faces the listener naturally while the referenced family member remains visible."


def prompt_for_family_line(row: dict, previous_reference: bool) -> str:
    ref_text = (
        "The shared family base scene is attached, and the previous family line image may also be attached. Preserve the same room, character identities, clothing, relative positions, lighting, and cartoon style."
        if previous_reference
        else "The shared family base scene is attached. Preserve the same room, character identities, clothing, relative positions, lighting, and cartoon style."
    )
    speaker, listener, _ = speaker_listener(row)
    return f"""Create one line-specific image for a spoken Kannada learning card.

Purpose:
This image is one sentence from the Chapter 1 family conversation covering cards 27-34. Use the attached shared family base scene as the visual anchor, but update gaze, pointing, posture, and focus so this specific sentence makes sense. The app will add the speech bubble and exact English/Kannada text after generation.

Chapter:
Chapter 1

Conversation id:
Conversation 3 continuation / family introduction

Conversation summary:
Kiran tells the teacher that the adult man is his father. The teacher asks about a girl, guesses Saroja, and Kiran explains that the girl is his younger sister Manju.

Full conversation excerpt:
{row['full_excerpt']}

Current line:
{row['row']}

Speaker:
{speaker}

Listener:
{listener}

What is happening in this exact image:
{family_line_action(row)} The sentence is: "{row['english']}"

English sentence for context only, do not render:
{row['english']}

Kannada sentence for context only, do not render:
{row['kannada']}

Romanized Kannada for context only, do not render:
{row['roman']}

Stable cast:
Teacher: adult Indian woman teacher in a sari, left foreground, kind expression.
Kiran: young Indian boy in a yellow shirt, center foreground.
Father: adult Indian man, right background, clearly older than Kiran.
Manju: young Indian girl, younger sister, right or center-right background. Manju is the only girl being discussed; do not create a separate Saroja character.

Scene continuity:
{ref_text}

Composition:
Keep all family characters recognizable and in roughly the same positions as the base scene. Change only gaze, hand gesture, slight body direction, and focus needed for this sentence. If the sentence mentions father, make the adult man the referenced person. If the sentence says she/her/Saroja/Manju/sister, make Manju the referenced person. Leave clean top space for a compact app-overlaid speech bubble. Do not draw speech bubbles, text, name badges, labels, signs, or blank label boxes.

Style:
Modern colorful children's storybook cartoon, warm Indian school setting, expressive characters, clean readable 16:9 composition.

Negative instructions:
No text, no letters, no captions, no UI, no watermarks, no fake writing, no chalk writing, no random symbols, no generated speech bubble, no generated name labels, no blank white label rectangles, no character named Saroja."""


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


def generate_base_image(api_key: str, prompt: str, references: list[Path]) -> bytes:
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
        "model": MODEL,
        "input": input_items,
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
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                body = json.loads(response.read().decode("utf-8"))
            image_data = find_image_data(body)
            if not image_data:
                raise RuntimeError(f"Gemini response did not include image data. Keys: {sorted(body.keys())}")
            return base64.b64decode(image_data)
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", errors="replace")
            if err.code in {429, 500, 502, 503, 504} and attempt < 3:
                time.sleep(20 + 20 * attempt)
                continue
            raise RuntimeError(f"Gemini image request failed: HTTP {err.code}: {detail}") from err
    raise RuntimeError("Gemini image request failed")


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


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_name_badge(
    draw: ImageDraw.ImageDraw,
    label: str,
    center_x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
) -> None:
    fill = BADGE_COLORS.get(label, (15, 23, 42))
    text_w, text_h = text_size(draw, label, font)
    pad_x = 18
    pad_y = 9
    box = (
        center_x - text_w // 2 - pad_x,
        y,
        center_x + text_w // 2 + pad_x,
        y + text_h + pad_y * 2,
    )
    shadow = (box[0] + 4, box[1] + 5, box[2] + 4, box[3] + 5)
    draw.rounded_rectangle(shadow, radius=18, fill=(0, 0, 0))
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=(255, 255, 255), width=3)
    draw.text((center_x - text_w // 2, y + pad_y - 1), label, font=font, fill=(255, 255, 255))


def overlay_name_badges(image: Image.Image, draw: ImageDraw.ImageDraw, row: dict) -> None:
    badge_font = ImageFont.truetype(LATIN_FONT, 32)
    for label, position in visible_characters(row):
        if position not in BADGE_POSITIONS:
            continue
        center_x, y = BADGE_POSITIONS[position]
        draw_name_badge(draw, label, center_x, y, badge_font)


def overlay_bubble(base_path: Path, final_path: Path, row: dict) -> None:
    image = Image.open(base_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    english_font = ImageFont.truetype(LATIN_FONT, 27)
    kannada_font = ImageFont.truetype(KANNADA_FONT, 30)
    speaker, _, _ = speaker_listener(row)
    left_speaker = speaker in {"Raju", "Adult teacher"} or row["speaker"] == "A"
    if is_family_target(row) and row["speaker"] == "B":
        box = (720, 42, 1260, 186)
        tail = (760, 212)
    elif is_family_target(row):
        box = (300, 34, 840, 178)
        tail = (420, 204)
    elif str(row["conversation"]) == "2" and row["speaker"] == "B":
        box = (720, 52, 1270, 202)
        tail = (1070, 310)
    elif str(row["conversation"]) == "2":
        box = (320, 30, 840, 166)
        tail = (360, 305)
    elif left_speaker:
        box = (58, 52, 570, 202)
        tail = (270, 310)
    else:
        box = (720, 52, 1270, 202)
        tail = (1070, 310)
    shadow = tuple(v + 7 for v in box)
    draw.rounded_rectangle(shadow, radius=20, fill=(0, 0, 0, 42))
    tail_base_x = min(max(tail[0], box[0] + 30), box[2] - 30)
    draw.polygon([(tail_base_x - 22, box[3] - 4), (tail_base_x + 22, box[3] - 4), tail], fill=(0, 0, 0))
    draw.rounded_rectangle(box, radius=20, fill=(255, 255, 255), outline=(37, 99, 235), width=4)
    draw.polygon([(tail_base_x - 22, box[3] - 4), (tail_base_x + 22, box[3] - 4), tail], fill=(255, 255, 255))
    draw.line([(tail_base_x - 22, box[3] - 4), tail, (tail_base_x + 22, box[3] - 4)], fill=(37, 99, 235), width=4)
    x = box[0] + 24
    y = box[1] + 17
    max_width = box[2] - box[0] - 48
    for line in wrapped_lines(row["english"], english_font, max_width):
        draw.text((x, y), line, font=english_font, fill=(15, 23, 42))
        y += 33
    y += 3
    kannada = row["kannada"] or row["roman"]
    for line in wrapped_lines(kannada, kannada_font, max_width):
        draw.text((x, y), line, font=kannada_font, fill=(15, 118, 110))
        y += 36
    overlay_name_badges(image, draw, row)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(final_path, quality=94)


def image_slug(row: dict) -> str:
    conv = str(row["conversation"]).lower().replace(" ", "-")
    return f"conversation-{conv}-{int(row['row']):02d}"


def update_chapter_visuals(rows: list[dict]) -> None:
    visuals = json.loads(VISUALS_PATH.read_text(encoding="utf-8")) if VISUALS_PATH.exists() else {}
    items = []
    for row in rows:
        slug = image_slug(row)
        items.append(
            {
                "img": f"images/gemini-chapter-visuals/chapter-01/{slug}.jpg",
                "conversation": row["conversation"],
                "row": row["row"],
                "english": row["english"],
                "roman": row["original_roman"],
                "theme_label": row["theme_label"],
            }
        )
    visuals["1"] = {
        "theme_label": "Greetings, introductions, names, and people",
        "items": items,
    }
    VISUALS_PATH.write_text(json.dumps(visuals, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    load_dotenv()
    api_key = find_existing_api_key()
    if not api_key:
        raise SystemExit("No GOOGLE_API_KEY/GEMINI_API_KEY found locally.")
    rows = chapter_one_rows()
    rows_by_conversation: dict[str, list[dict]] = {}
    for row in rows:
        rows_by_conversation.setdefault(str(row["conversation"]), []).append(row)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Using {MODEL}; generating {len(rows)} Chapter 1 images. API key loaded locally and masked.")
    previous_base: Path | None = None
    anchor_base: Path | None = None
    previous_conversation: str | None = None
    conversation_2_previous_line: Path | None = None
    family_previous_line: Path | None = None
    for index, row in enumerate(rows, 1):
        slug = image_slug(row)
        shared_conversation = str(row["conversation"]) == "2"
        family_conversation = is_family_target(row)
        shared_base_path = OUT_DIR / "conversation-2-shared-scene-base.jpg"
        family_base_path = OUT_DIR / "conversation-family-shared-scene-base.jpg"
        base_path = OUT_DIR / f"{slug}-base.jpg"
        final_path = OUT_DIR / f"{slug}.jpg"
        prompt_path = OUT_DIR / f"{slug}.prompt.txt"
        same_conversation = row["conversation"] == previous_conversation
        references: list[Path] = []
        if shared_conversation:
            if not shared_base_path.exists():
                shared_prompt = shared_base_prompt_for_conversation("2", rows_by_conversation["2"])
                (OUT_DIR / "conversation-2-shared-scene.prompt.txt").write_text(shared_prompt, encoding="utf-8")
                print(f"[{index}/{len(rows)}] Generating conversation-2 shared scene with 0 reference image(s)...", flush=True)
                shared_base_path.write_bytes(generate_base_image(api_key, shared_prompt, []))
                time.sleep(0.4)
            references.append(shared_base_path)
            if conversation_2_previous_line and conversation_2_previous_line.exists():
                references.append(conversation_2_previous_line)
        elif family_conversation:
            family_rows = [candidate for candidate in rows if is_family_target(candidate)]
            if not family_base_path.exists():
                shared_prompt = shared_base_prompt_for_conversation("family", family_rows)
                (OUT_DIR / "conversation-family-shared-scene.prompt.txt").write_text(shared_prompt, encoding="utf-8")
                print(f"[{index}/{len(rows)}] Generating family shared scene with 0 reference image(s)...", flush=True)
                family_base_path.write_bytes(generate_base_image(api_key, shared_prompt, []))
                time.sleep(0.4)
            references.append(family_base_path)
            if family_previous_line and family_previous_line.exists():
                references.append(family_previous_line)
        elif same_conversation and previous_base and previous_base.exists():
            references.append(previous_base)
        if not shared_conversation and not family_conversation and anchor_base and anchor_base.exists() and anchor_base not in references:
            references.append(anchor_base)
        prompt = (
            prompt_for_conversation_2_line(row, bool(references))
            if shared_conversation
            else prompt_for_family_line(row, bool(references))
            if family_conversation
            else prompt_for(row, bool(references))
        )
        prompt_path.write_text(prompt, encoding="utf-8")
        if not base_path.exists():
            print(f"[{index}/{len(rows)}] Generating {slug} with {len(references)} reference image(s)...", flush=True)
            base_path.write_bytes(generate_base_image(api_key, prompt, references))
            time.sleep(0.4)
        else:
            print(f"[{index}/{len(rows)}] Reusing {base_path}", flush=True)
        overlay_bubble(base_path, final_path, row)
        if anchor_base is None and not shared_conversation and not family_conversation:
            anchor_base = base_path
        if not shared_conversation and not family_conversation:
            previous_base = base_path
        elif shared_conversation:
            conversation_2_previous_line = base_path
        else:
            family_previous_line = base_path
        previous_conversation = row["conversation"]
    update_chapter_visuals(rows)
    print(f"Wrote Chapter 1 image set to {OUT_DIR}")
    print(f"Updated {VISUALS_PATH}")


if __name__ == "__main__":
    main()
