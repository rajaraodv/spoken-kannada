#!/usr/bin/env python3
"""Build a page-by-page transcription review HTML for Spoken Kannada.

This intentionally avoids global chapter reorganization. The PDF frequently
extracts as "all romanized Kannada in the left column, then all English in the
right column", so pairing is safest when done page by page.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from pypdf import PdfReader


PDF_PATH = Path("/Users/rajaraodv/Downloads/Spoken Kannada - Kannada Sahitya Parishat_text.pdf")
DATA_PATH = Path("data/page_by_page_conversations.json")
HTML_PATH = Path("public/conversations-page-by-page.html")
CHAPTER_DIR = Path("public/chapters")
CHAPTER_VISUALS_PATH = Path("data/chapter_visuals.json")
SARVAM_CORRECTIONS_PATH = Path("data/sarvam_corrections_all_chapters.json")
SARVAM_LEGACY_CORRECTIONS_PATH = Path("data/sarvam_corrections_chapters_01_02.json")
SARVAM_MANUAL_OVERRIDES_PATH = Path("data/sarvam_manual_overrides_chapters_01_02.json")
GLOBAL_PHRASE_OVERRIDES = {
    "good morning": {
        "sarvam_kannada": "ನಮಸ್ಕಾರ",
        "sarvam_roman": "Namaskara",
    },
    "how are you": {
        "sarvam_kannada": "ಚೆನ್ನಾಗಿದ್ದೀರಾ?",
        "sarvam_roman": "Chennagiddeera?",
    },
    "please come vasu be seated": {
        "sarvam_kannada": "ಬನ್ನಿ, ವಾಸು, ಕುಳಿತುಕೊಳ್ಳಿ.",
        "sarvam_roman": "Banni, Vaasu, kulitukolli.",
    },
}
PAGE_IMAGES = {
    9: {
        "src": "images/chapter-1-meeting-people-cartoon.png",
        "alt": "Cartoon illustration for Chapter 1 Conversation 1 showing English lines above romanized Kannada phrases.",
        "caption": "Chapter 1 visual conversation: read the English, then say the Kannada underneath.",
    }
}
CHAPTER_1_VISUAL_LINES = [
    {
        "img": "images/chapter-1-snippets/01-good-morning.png",
        "conversation": "1",
        "row": 1,
        "title": "Greeting each other",
        "english": "Good Morning.",
        "roman": "namaskaara",
        "speak_kn": "ನಮಸ್ಕಾರ",
    },
    {
        "img": "images/chapter-1-snippets/02-i-am-raju.png",
        "conversation": "1",
        "row": 3,
        "title": "Introducing yourself",
        "english": "I am Raju.",
        "roman": "naanu raju",
        "speak_kn": "ನಾನು ರಾಜು",
    },
    {
        "img": "images/chapter-1-snippets/03-he-is-mohan.png",
        "conversation": "1",
        "row": 4,
        "title": "Introducing Mohan",
        "english": "He is Mohan.",
        "roman": "ivaru moohan",
        "speak_kn": "ಇವರು ಮೋಹನ್",
        "note": "ivaru points to this person nearby. In the picture, Mohan is close to the speakers.",
    },
    {
        "img": "images/chapter-1-snippets/04-who-are-you.png",
        "conversation": "1",
        "row": 5,
        "title": "Asking who someone is",
        "english": "Who are you?",
        "roman": "niivu yaaru?",
        "speak_kn": "ನೀವು ಯಾರು?",
    },
    {
        "img": "images/chapter-1-snippets/05-i-am-shekhar.png",
        "conversation": "1",
        "row": 6,
        "title": "Shekhar answers",
        "english": "I am Shekhar.",
        "roman": "naanu seekhar",
        "speak_kn": "ನಾನು ಶೇಖರ್",
    },
    {
        "img": "images/chapter-1-snippets/06-who-is-she.png",
        "conversation": "1",
        "row": 7,
        "title": "Asking about Sheela",
        "english": "Who is she?",
        "roman": "avaru yaaru?",
        "speak_kn": "ಅವರು ಯಾರು?",
        "note": "avaru points to that person farther away. Raju is asking about Sheela across the scene.",
    },
    {
        "img": "images/chapter-1-snippets/07-she-is-sheela.png",
        "conversation": "1",
        "row": 8,
        "title": "Introducing Sheela",
        "english": "She is Sheela.",
        "roman": "avaru siila",
        "speak_kn": "ಅವರು ಶೀಲಾ",
        "note": "avaru means that person in this context, so Sheela stays visually farther away.",
    },
    {
        "img": "images/chapter-1-snippets/08-he-is-shankar.png",
        "conversation": "1",
        "row": 9,
        "title": "Introducing Shankar",
        "english": "He is Shankar.",
        "roman": "ivaru sankar",
        "speak_kn": "ಇವರು ಶಂಕರ್",
        "note": "ivaru means this person nearby. Shankar is drawn closer to the speaker than Sheela was.",
    },
]


ENGLISH_STARTERS = (
    "Good ",
    "Hello",
    "Please",
    "I ",
    "I'm ",
    "Is ",
    "Isn",
    "Are ",
    "Aren't ",
    "Do ",
    "Don't ",
    "Don’t ",
    "Does ",
    "Did ",
    "Will ",
    "Would ",
    "When ",
    "Where ",
    "Which ",
    "Who ",
    "Whose ",
    "What ",
    "What",
    "Why ",
    "How ",
    "Yes",
    "No",
    "Oh",
    "Well",
    "That ",
    "This ",
    "Those ",
    "These ",
    "There ",
    "It ",
    "It's ",
    "It’s ",
    "He ",
    "She ",
    "They ",
    "Mummy",
    "My ",
    "Look ",
    "If ",
    "About ",
    "For ",
    "At ",
    "In ",
    "Of ",
    "Rs.",
    "Nothing",
    "Two ",
    "Three",
    "One ",
)

ENGLISH_WORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "and",
    "are",
    "at",
    "be",
    "because",
    "but",
    "by",
    "children",
    "class",
    "come",
    "did",
    "do",
    "does",
    "doing",
    "for",
    "from",
    "go",
    "good",
    "had",
    "has",
    "have",
    "he",
    "here",
    "his",
    "home",
    "house",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "my",
    "no",
    "not",
    "of",
    "one",
    "per",
    "please",
    "she",
    "sir",
    "that",
    "the",
    "there",
    "this",
    "to",
    "very",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "will",
    "with",
    "yes",
    "you",
    "your",
}


@dataclass
class Row:
    speaker: str
    roman: str
    english: str


@dataclass
class PageConversation:
    page: int
    lesson: int | None
    number: str
    rows: list[Row]
    raw_lines: list[str]


def clean_lines(text: str) -> list[str]:
    lines: list[str] = []
    for original in text.replace("\x00", "").splitlines():
        line = re.sub(r"\s+", " ", original).strip()
        if not line:
            continue
        if line in {"Digitized by Google", "Digitized by", "Original from", "UNIVERSITY OF MICHIGAN"}:
            continue
        if "UNIVERSITY OF MICHIGAN" in line or line.startswith("Digitized by Google Original from"):
            continue
        lines.append(line)
    return lines


def split_inline_translation(text: str) -> tuple[str, str]:
    best: int | None = None
    for starter in ENGLISH_STARTERS:
        index = text.find(starter)
        if index > 0 and (best is None or index < best):
            best = index
    if best is None:
        return text.strip(), ""
    return text[:best].strip(" ;:-"), text[best:].strip()


def looks_english(line: str) -> bool:
    if any(line.startswith(starter) for starter in ENGLISH_STARTERS):
        return True
    words = re.findall(r"[A-Za-z']+", line.lower())
    if not words:
        return False
    hits = sum(1 for word in words if word in ENGLISH_WORDS)
    return hits >= 2 and hits / len(words) >= 0.34


def is_noise(line: str) -> bool:
    if re.fullmatch(r"\d+", line):
        return True
    if line in {"■", "•"}:
        return True
    if re.fullmatch(r"[<> a]+", line):
        return True
    if re.match(r"^Lesson\s+\d+\b", line):
        return True
    if re.match(r"^(Vocabulary|Vacobulary|Vocabalary|Exercises)\b", line, re.I):
        return True
    return False


def conversation_marker(line: str) -> str | None:
    match = re.match(r"^Conversation\s*[-:;]?\s*(\d+|I|!)?\b", line, re.I)
    if not match:
        return None
    value = match.group(1)
    if not value:
        return "1"
    if value in {"I", "!"}:
        return "1"
    return value


def lesson_number(lines: list[str]) -> int | None:
    for line in lines:
        match = re.match(r"^Lesson\s+(\d+)\b", line)
        if match:
            return int(match.group(1))
    return None


def add_english(lines: list[str], line: str) -> None:
    line = line.strip()
    if not line:
        return
    lines.append(line)


def should_join_english(previous: str, current: str) -> bool:
    if previous.lower().strip(" ,") in {"yes", "no"}:
        return False
    if previous.endswith(("?", "!", ".")) and current.lower().startswith(("oh", "yes", "no")):
        return False
    if previous.lower().startswith(("one son", "two sons", "three sons")):
        return False
    if previous.endswith(("-", ",")):
        return True
    if not previous.endswith((".", "?", "!", ";", ":")) and not any(
        current.startswith(starter) for starter in ENGLISH_STARTERS
    ):
        return True
    if current[:1].islower():
        return True
    return False


def should_join_roman(previous: str, current: str) -> bool:
    if current.startswith(("alvaa", "ivattu noo", "adakke ")):
        return True
    return False


def parse_page(page: int, lines: list[str]) -> list[PageConversation]:
    lesson = lesson_number(lines)
    current_conv = "Continuation"
    current_speaker = ""
    romans: list[tuple[str, str, str, str]] = []
    english: list[str] = []
    conversations: list[PageConversation] = []
    saw_english = False
    saw_conversation = False

    def add_roman(conv: str, speaker: str, roman: str, fixed_english: str = "") -> None:
        nonlocal romans
        roman = roman.strip()
        if not roman:
            return
        if (
            not fixed_english
            and romans
            and romans[-1][0] == conv
            and romans[-1][3] == ""
            and should_join_roman(romans[-1][2], roman)
        ):
            last_conv, last_speaker, previous, last_english = romans[-1]
            romans[-1] = (last_conv, last_speaker, f"{previous} {roman}", last_english)
            return
        romans.append((conv, speaker, roman, fixed_english))

    def flush_segment() -> None:
        nonlocal romans, english
        if not romans:
            english = []
            return
        by_conv: dict[str, list[Row]] = {}
        english_index = 0
        for conv, speaker, roman, fixed_english in romans:
            if fixed_english:
                english_line = fixed_english
            else:
                english_line = english[english_index] if english_index < len(english) else ""
                english_index += 1
            by_conv.setdefault(conv, []).append(Row(speaker=speaker, roman=roman, english=english_line))
        for conv, rows in by_conv.items():
            conversations.append(
                PageConversation(page=page, lesson=lesson, number=conv, rows=rows, raw_lines=lines)
            )
        romans = []
        english = []

    for line in lines:
        marker = conversation_marker(line)
        if marker:
            if saw_english:
                flush_segment()
                saw_english = False
            current_conv = marker
            current_speaker = ""
            saw_conversation = True
            continue
        if is_noise(line):
            continue
        if "—" in line or " _ " in line:
            continue

        speaker_match = re.match(r"^([ABC])\s*[:;]\s*(.*)$", line)
        colon_continuation = re.match(r"^:\s*(.*)$", line)
        if speaker_match and not saw_english:
            current_speaker = speaker_match.group(1)
            roman, inline_english = split_inline_translation(speaker_match.group(2))
            add_roman(current_conv, current_speaker, roman, inline_english)
            continue
        if colon_continuation and not saw_english:
            roman, inline_english = split_inline_translation(colon_continuation.group(1))
            add_roman(current_conv, current_speaker, roman, inline_english)
            continue

        roman_part, inline_english = split_inline_translation(line)
        if inline_english and not saw_english:
            add_roman(current_conv, current_speaker, roman_part, inline_english)
            continue

        if looks_english(line):
            saw_english = True
            add_english(english, line)
            continue

        if saw_english:
            add_english(english, line)
            continue

        if not saw_conversation and not speaker_match and not romans:
            continue
        add_roman(current_conv, current_speaker, roman_part)

    flush_segment()

    return conversations


def extract() -> list[PageConversation]:
    reader = PdfReader(str(PDF_PATH))
    conversations: list[PageConversation] = []
    for page_index, page in enumerate(reader.pages, 1):
        lines = clean_lines(page.extract_text() or "")
        if not any("Conversation" in line for line in lines) and not any(
            re.match(r"^[ABC]\s*[:;]", line) for line in lines
        ):
            continue
        conversations.extend(parse_page(page_index, lines))
    return conversations


LESSON_THEMES = {
    1: "Greetings, names, family",
    2: "Introductions, this/that, house/book",
    3: "Classes, possessives, books/pens",
    4: "House, rent, family counts",
    5: "Hotels, holidays, dates",
    6: "Relatives, comparisons, town places",
    7: "Directions, transport, existence",
    8: "Home visits, relatives, locations",
    9: "Past locations: was/were",
    10: "Food, weather, descriptions",
    11: "Going/coming, schedules, habits",
    12: "Eating, animals, present actions",
    13: "Travel and completed actions",
    14: "Illness, accident, medicine",
    15: "Renting, shopping, college, languages",
    16: "Duties, permission, obligation",
    17: "Commands, tasks, ought-to",
    18: "Market plans and hospitality",
    19: "Advice, quitting, child behavior",
    20: "Conditionals, travel, promises",
    21: "Purpose/reasons, education/snacks",
    22: "Perfect tense: awake, absence, dispatch",
    23: "Past perfect travel and treatment",
    24: "Continuous actions and occupations",
    25: "Past continuous: garden, illness, farming",
    26: "Relative clauses: office, song, school",
    27: "Groups, learners, readers",
    28: "Time clauses with when",
    29: "Until/after clauses, studying",
    30: "Hypothetical conditionals",
    31: "Comparisons, manner, passive/made-by",
}


def chapter_slug(chapter: int) -> str:
    return f"chapter-{chapter:02d}.html"


def assign_chapters(conversations: list[PageConversation]) -> dict[int, list[PageConversation]]:
    chapters: dict[int, list[PageConversation]] = {}
    current: int | None = None
    for conversation in conversations:
        if conversation.lesson is not None:
            current = conversation.lesson
        if current is None:
            continue
        chapters.setdefault(current, []).append(conversation)
    return dict(sorted(chapters.items()))


def load_chapter_visuals() -> dict[str, dict]:
    if not CHAPTER_VISUALS_PATH.exists():
        return {}
    return json.loads(CHAPTER_VISUALS_PATH.read_text(encoding="utf-8"))


def load_sarvam_corrections() -> dict[str, dict]:
    if SARVAM_CORRECTIONS_PATH.exists():
        corrections = json.loads(SARVAM_CORRECTIONS_PATH.read_text(encoding="utf-8"))
    elif SARVAM_LEGACY_CORRECTIONS_PATH.exists():
        corrections = json.loads(SARVAM_LEGACY_CORRECTIONS_PATH.read_text(encoding="utf-8"))
    else:
        corrections = {}
    for key, correction in list(corrections.items()):
        phrase_key = re.sub(r"[^a-z0-9]+", " ", str(correction.get("english", "")).lower()).strip()
        override = GLOBAL_PHRASE_OVERRIDES.get(phrase_key)
        if not override:
            continue
        merged = dict(correction)
        merged.update(override)
        merged["source"] = f"{merged.get('source', 'sarvam_translate_mayura_v1')}+global_phrase_override"
        corrections[key] = merged
    if SARVAM_MANUAL_OVERRIDES_PATH.exists():
        overrides = json.loads(SARVAM_MANUAL_OVERRIDES_PATH.read_text(encoding="utf-8"))
        for key, override in overrides.items():
            merged = dict(corrections.get(key, {}))
            merged.update(override)
            merged["source"] = f"{merged.get('source', 'sarvam_translate_mayura_v1')}+manual_override"
            corrections[key] = merged
    return corrections


def correction_key(chapter: int, conversation: str, row: int) -> str:
    return f"chapter-{chapter:02d}:conversation-{conversation}:row-{row:02d}"


def correction_for(corrections: dict[str, dict], chapter: int, conversation: str, row: int) -> dict | None:
    return corrections.get(correction_key(chapter, str(conversation), int(row)))


def with_original_deictic(correction: dict | None, original_roman: str) -> dict | None:
    if not correction:
        return None
    cleaned = re.sub(r"[^A-Za-z]+", " ", original_roman).strip().lower()
    first = cleaned.split()[0] if cleaned else ""
    replacements = {
        "ivaru": ("Avaru", "Ivaru", "ಅವರು", "ಇವರು"),
        "ivara": ("Avara", "Ivara", "ಅವರ", "ಇವರ"),
        "idu": ("Adu", "Idu", "ಅದು", "ಇದು"),
        "idara": ("Adara", "Idara", "ಅದರ", "ಇದರ"),
    }
    if first not in replacements:
        return correction
    roman_from, roman_to, kn_from, kn_to = replacements[first]
    adjusted = dict(correction)
    adjusted["sarvam_roman"] = re.sub(rf"^{roman_from}\b", roman_to, adjusted.get("sarvam_roman", ""), flags=re.I)
    adjusted["sarvam_kannada"] = adjusted.get("sarvam_kannada", "").replace(kn_from, kn_to, 1)
    return adjusted


def page_shell(title: str, body: str, relative_prefix: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --ink: #1d1d1f;
      --muted: #6e6e73;
      --line: #d2d2d7;
      --paper: #f5f5f7;
      --panel: #ffffff;
      --soft: #f9f9fb;
      --accent: #0071e3;
      --accent-soft: rgba(0, 113, 227, .10);
      --kannada: #167d6b;
      --practice: #1d1d1f;
      --warn: #8a4b1f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 24% 0%, rgba(255, 255, 255, .95), transparent 34%),
        linear-gradient(135deg, #f7f8fb 0%, #fffaf2 100%);
      line-height: 1.5;
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 32px 18px 72px; }}
    main:has(.learning-app) {{ max-width: none; padding: 0; }}
    h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 3.7rem); line-height: 1; letter-spacing: 0; }}
    .intro {{ max-width: 860px; color: var(--muted); }}
    .note {{ border-left: 4px solid var(--warn); background: #fff7ed; padding: 12px 14px; max-width: 920px; }}
    .chapter-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; margin-top: 28px; }}
    .chapter-card {{ display: grid; gap: 8px; text-decoration: none; color: inherit; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }}
    .chapter-card strong {{ font-size: 1.1rem; }}
    .chapter-card span {{ color: var(--muted); }}
    .topbar {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between; margin-bottom: 22px; }}
    .topbar a {{ color: var(--accent); font-weight: 800; text-decoration: none; }}
    .chapter-nav {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 22px 0; }}
    .chapter-nav a {{ color: var(--ink); text-decoration: none; border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; background: var(--panel); }}
    nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 24px 0 36px; }}
    nav a {{
      color: var(--ink); text-decoration: none; background: var(--panel);
      border: 1px solid var(--line); border-radius: 8px; padding: 7px 10px;
    }}
    section {{ margin: 42px 0; }}
    h2 {{ margin: 0 0 14px; font-size: 1.55rem; }}
    .app-main {{
      max-width: none;
      padding: 0;
    }}
    .learning-app {{
      display: grid;
      grid-template-columns: 116px minmax(0, 1fr);
      min-height: 100vh;
    }}
    .side-rail {{
      position: sticky;
      top: 0;
      height: 100vh;
      padding: 30px 18px;
      display: grid;
      grid-template-rows: auto 1fr auto;
      justify-items: center;
      gap: 28px;
      background: rgba(255, 255, 255, .72);
      border-right: 1px solid rgba(210, 210, 215, .72);
      box-shadow: 12px 0 40px rgba(29, 29, 31, .04);
      backdrop-filter: blur(22px);
    }}
    .rail-logo {{
      width: 54px;
      height: 54px;
      border-radius: 16px;
      display: grid;
      place-items: center;
      color: #e75f1b;
      background: #ffffff;
      border: 2px solid rgba(231, 95, 27, .35);
      box-shadow: 0 10px 24px rgba(231, 95, 27, .10);
      font-size: 1.65rem;
      text-decoration: none;
    }}
    .chapter-rail {{
      width: 100%;
      display: grid;
      gap: 8px;
      overflow-y: auto;
      padding: 2px 0;
      scrollbar-width: thin;
    }}
    .chapter-rail a {{
      display: grid;
      place-items: center;
      min-height: 44px;
      border-radius: 14px;
      color: #6b7280;
      text-decoration: none;
      font-weight: 800;
      border: 1px solid transparent;
    }}
    .chapter-rail a.active {{
      color: #e75f1b;
      background: #fff2e9;
      border-color: rgba(231, 95, 27, .16);
      box-shadow: inset 0 1px 0 rgba(255,255,255,.74);
    }}
    .rail-tools {{
      display: grid;
      gap: 18px;
      width: 100%;
      color: var(--muted);
      font-size: .82rem;
      font-weight: 700;
      text-align: center;
    }}
    .rail-tool {{
      display: grid;
      justify-items: center;
      gap: 5px;
      text-decoration: none;
      color: inherit;
    }}
    .rail-tool .avatar {{
      width: 44px;
      height: 44px;
      display: grid;
      place-items: center;
      border-radius: 999px;
      background: #ffe2a7;
      font-size: 1.45rem;
    }}
    .lesson-workspace {{
      width: min(100%, 1180px);
      margin: 0 auto;
      padding: 44px 32px 72px;
    }}
    .lesson-header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 330px;
      gap: 28px;
      align-items: start;
      margin-bottom: 28px;
    }}
    .lesson-kicker {{
      margin: 0 0 6px;
      color: #e75f1b;
      font-weight: 850;
      font-size: .95rem;
    }}
    .lesson-title {{
      margin: 0;
      font-size: clamp(2.1rem, 4.5vw, 3.35rem);
      line-height: 1.03;
      font-weight: 850;
      color: #111827;
    }}
    .lesson-subtitle {{
      max-width: 680px;
      margin: 14px 0 0;
      color: #5d6470;
      font-size: clamp(1rem, 1.8vw, 1.14rem);
      line-height: 1.6;
    }}
    .progress-card {{
      display: grid;
      grid-template-columns: 58px minmax(0, 1fr);
      gap: 16px;
      align-items: center;
      padding: 16px 18px;
      border: 1px solid rgba(210, 210, 215, .78);
      border-radius: 20px;
      background: rgba(255, 255, 255, .72);
      box-shadow: 0 16px 34px rgba(29, 29, 31, .06);
      backdrop-filter: blur(18px);
    }}
    .progress-icon {{
      width: 54px;
      height: 54px;
      border-radius: 999px;
      display: grid;
      place-items: center;
      color: #d97706;
      background: #fff7ed;
      border: 1px solid rgba(217, 119, 6, .16);
      font-size: 1.55rem;
    }}
    .progress-label {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      color: var(--muted);
      font-weight: 700;
    }}
    .progress-count {{
      color: var(--ink);
      font-weight: 850;
    }}
    .progress-track {{
      height: 10px;
      margin-top: 10px;
      border-radius: 999px;
      background: #e5e7eb;
      overflow: hidden;
    }}
    .progress-fill {{
      width: var(--progress, 8%);
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, #42b883, #a4d65e);
      transition: width .22s ease;
    }}
    .lesson-controls {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 18px;
      margin: 0 0 26px;
    }}
    .scene-pager {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .scene-pill {{
      min-width: 128px;
      padding: 11px 16px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: rgba(255, 255, 255, .78);
      color: #4b5563;
      text-align: center;
      font-weight: 800;
      box-shadow: 0 8px 18px rgba(29, 29, 31, .04);
    }}
    .scene-arrow {{
      width: 48px;
      height: 48px;
      border: 0;
      border-radius: 999px;
      display: grid;
      place-items: center;
      background: rgba(255,255,255,.72);
      color: #9ca3af;
      font-size: 1.35rem;
      font-weight: 900;
      cursor: pointer;
      box-shadow: 0 10px 22px rgba(29, 29, 31, .06);
    }}
    .scene-arrow.next {{
      color: #ffffff;
      background: linear-gradient(135deg, #25a46b, #147b5f);
      box-shadow: 0 14px 24px rgba(20, 123, 95, .22);
    }}
    .scene-arrow:disabled {{
      opacity: .48;
      cursor: default;
    }}
    .visual-practice {{
      margin: 0 0 16px;
    }}
    .visual-practice h3 {{ margin: 0 0 4px; font-size: 1.2rem; }}
    .visual-practice > p {{ margin: 0 0 14px; color: var(--muted); }}
    .snippet-stack {{
      display: grid;
      gap: 22px;
    }}
    .snippet-card {{
      position: relative;
      border: 1px solid var(--line);
      border-radius: 26px;
      overflow: hidden;
      background: var(--panel);
      box-shadow: 0 18px 48px rgba(0, 0, 0, .08);
    }}
    .snippet-card.correct {{
      border-color: rgba(52, 199, 89, .55);
      box-shadow: 0 22px 56px rgba(52, 199, 89, .18);
    }}
    .snippet-card.retry-shake {{
      animation: retry-shake .32s ease;
    }}
    .snippet-card img {{
      display: block;
      width: 100%;
      height: auto;
      min-height: 0;
      object-fit: contain;
      object-position: center;
      background: var(--soft);
    }}
    .snippet-card svg {{ width: 100%; height: auto; display: block; }}
    .snippet-body {{
      padding: clamp(18px, 3vw, 28px);
      background: rgba(255, 255, 255, .92);
      border-bottom: 1px solid var(--line);
    }}
    .snippet-body h4 {{
      margin: 0;
      color: #4b5563;
      font-size: clamp(1rem, 1.7vw, 1.18rem);
      font-weight: 800;
    }}
    .snippet-heading {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 24px;
    }}
    .snippet-topic {{
      display: flex;
      align-items: center;
      gap: 14px;
      min-width: 0;
    }}
    .snippet-topic-icon {{
      width: 42px;
      height: 42px;
      flex: 0 0 auto;
      border-radius: 999px;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, #43c076, #17825f);
      color: white;
      box-shadow: 0 12px 22px rgba(23, 130, 95, .20);
    }}
    .new-pill {{
      flex: 0 0 auto;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      border-radius: 999px;
      background: #eaf8ef;
      color: #198754;
      border: 1px solid rgba(25, 135, 84, .14);
      font-size: .9rem;
      font-weight: 800;
    }}
    .snippet-line {{
      display: grid;
      gap: 8px;
      margin: 0 0 22px;
      padding: clamp(28px, 5vw, 48px);
      border: 1px solid rgba(0, 0, 0, .08);
      border-radius: 24px;
      background: #ffffff;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, .72), 0 10px 26px rgba(29,29,31,.035);
    }}
    .snippet-line strong {{
      font-size: clamp(2.6rem, 5.8vw, 4.1rem);
      line-height: 1.04;
      color: var(--ink);
      font-weight: 850;
    }}
    .snippet-line span {{
      color: var(--kannada);
      font-weight: 760;
      font-size: clamp(1.45rem, 3.4vw, 2.15rem);
      line-height: 1.15;
      font-style: italic;
    }}
    .kannada-script {{
      color: #c7511a;
      font-size: clamp(2.1rem, 4.8vw, 3.65rem);
      font-weight: 850;
      line-height: 1.18;
    }}
    .original-roman {{
      margin: 0 0 16px;
      color: var(--muted);
      font-size: .95rem;
      font-weight: 650;
    }}
    .grammar-note {{
      margin: -2px 0 12px;
      color: var(--muted);
      font-size: .96rem;
      line-height: 1.45;
    }}
    .grammar-note strong {{ color: var(--ink); }}
    .listen-row {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 26px; align-items: center; }}
    .speak-btn {{
      border: 1px solid rgba(0, 0, 0, .10);
      background: #ffffff;
      color: var(--ink);
      border-radius: 16px;
      padding: 18px 22px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      font: inherit;
      font-size: clamp(1rem, 2.1vw, 1.18rem);
      font-weight: 850;
      cursor: pointer;
      min-width: 0;
      box-shadow: 0 10px 24px rgba(29, 29, 31, .05);
      transition: transform .16s ease, box-shadow .16s ease, background .16s ease, border-color .16s ease;
    }}
    .speak-btn:hover {{
      transform: translateY(-1px);
      box-shadow: 0 8px 18px rgba(0, 0, 0, .08);
    }}
    .speak-btn[data-lang="en-IN"] {{
      color: #1764d8;
      border-color: rgba(23, 100, 216, .22);
      background: #eef5ff;
    }}
    .speak-btn[data-lang="kn-IN"] {{
      color: #177f62;
      border-color: rgba(23, 127, 98, .22);
      background: #eef8f3;
    }}
    .practice-btn {{
      color: #5b2fc6;
      border-color: rgba(91, 47, 198, .22);
      background: #f4efff;
      min-width: 0;
    }}
    .practice-btn:hover {{ box-shadow: 0 10px 22px rgba(91, 47, 198, .12); }}
    .speak-btn:active {{ transform: translateY(1px); }}
    .speak-btn[disabled] {{ opacity: .6; cursor: wait; }}
    .btn-icon {{
      width: 34px;
      height: 34px;
      border-radius: 999px;
      display: inline-grid;
      place-items: center;
      flex: 0 0 auto;
      color: #ffffff;
      font-size: .95rem;
      line-height: 1;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.32);
    }}
    .speak-btn[data-lang="en-IN"] .btn-icon {{ background: #1764d8; }}
    .speak-btn[data-lang="kn-IN"] .btn-icon {{ background: #177f62; }}
    .practice-btn .btn-icon {{ background: #6d3bd1; }}
    .practice-feedback {{
      display: none;
      margin-top: 12px;
      padding: 13px 15px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: #f9f9fb;
      color: var(--muted);
      font-weight: 700;
    }}
    .practice-feedback.show {{ display: block; }}
    .practice-feedback.good {{
      border: 3px solid rgba(22, 163, 74, .65);
      background:
        radial-gradient(circle at 12% 18%, rgba(250, 204, 21, .42), transparent 24%),
        radial-gradient(circle at 88% 18%, rgba(45, 212, 191, .36), transparent 26%),
        linear-gradient(135deg, #f0fdf4, #ecfeff);
      color: #166534;
      font-size: clamp(1.45rem, 4vw, 2.45rem);
      line-height: 1.12;
      padding: 22px 24px;
      box-shadow: 0 14px 30px rgba(22, 163, 74, .18);
      animation: success-pop .44s cubic-bezier(.2, 1.35, .35, 1);
    }}
    .practice-feedback.retry {{
      border-color: rgba(255, 149, 0, .38);
      background: #fff8ed;
      color: #8a4b1f;
      animation: retry-nudge .28s ease;
    }}
    .practice-btn.correct {{
      background: #34c759;
      border-color: #34c759;
      color: #ffffff;
      transform: scale(1.02);
      box-shadow: 0 12px 26px rgba(52, 199, 89, .22);
    }}
    .celebration-sprinkles {{
      pointer-events: none;
      position: absolute;
      inset: 0;
      overflow: hidden;
      z-index: 3;
    }}
    .celebration-sprinkles span {{
      position: absolute;
      top: 44%;
      left: 50%;
      width: 12px;
      height: 22px;
      border-radius: 3px;
      background: var(--sprinkle-color, #facc15);
      transform: translate(-50%, -50%) rotate(var(--sprinkle-rotate, 0deg));
      animation: sprinkle-burst .95s ease-out forwards;
      animation-delay: var(--sprinkle-delay, 0s);
    }}
    @keyframes success-pop {{
      0% {{ transform: scale(.86); opacity: .2; }}
      70% {{ transform: scale(1.035); opacity: 1; }}
      100% {{ transform: scale(1); opacity: 1; }}
    }}
    @keyframes retry-shake {{
      0%, 100% {{ transform: translateX(0); }}
      22% {{ transform: translateX(-6px); }}
      48% {{ transform: translateX(5px); }}
      72% {{ transform: translateX(-3px); }}
    }}
    @keyframes retry-nudge {{
      0% {{ transform: scale(.98); opacity: .65; }}
      100% {{ transform: scale(1); opacity: 1; }}
    }}
    @keyframes sprinkle-burst {{
      0% {{
        opacity: 1;
        transform: translate(-50%, -50%) scale(.7) rotate(var(--sprinkle-rotate, 0deg));
      }}
      100% {{
        opacity: 0;
        transform:
          translate(
            calc(-50% + var(--sprinkle-x, 0px)),
            calc(-50% + var(--sprinkle-y, -120px))
          )
          scale(1.1)
          rotate(calc(var(--sprinkle-rotate, 0deg) + 220deg));
      }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .practice-feedback.good,
      .celebration-sprinkles span {{
        animation: none;
      }}
    }}
    .voice-toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin: 0;
      color: var(--muted);
      font-weight: 800;
    }}
    .voice-toolbar select {{
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 42px 12px 18px;
      background: rgba(255,255,255,.78);
      color: var(--ink);
      font: inherit;
      font-weight: 800;
      box-shadow: 0 8px 18px rgba(29, 29, 31, .05);
    }}
    .voice-wave {{ color: #5b5ff0; font-weight: 900; font-size: 1.4rem; }}
    .lesson-tip {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin: 28px 0 0;
      padding: 18px 22px;
      border-radius: 14px;
      border: 1px solid rgba(245, 158, 11, .32);
      background: #fff8e9;
      color: #4b5563;
      font-weight: 650;
    }}
    .lesson-tip strong {{ color: var(--ink); }}
    .tip-chip {{
      display: inline-flex;
      gap: 8px;
      align-items: center;
      white-space: nowrap;
      padding: 10px 18px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #ffffff;
      color: var(--ink);
      font-weight: 850;
      box-shadow: 0 8px 18px rgba(29,29,31,.06);
    }}
    .source-panel {{
      margin-top: 26px;
      padding: 0;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, .72);
      overflow: hidden;
    }}
    .source-panel > summary {{
      padding: 18px 22px;
      color: var(--ink);
      font-weight: 850;
    }}
    .source-panel section {{
      margin: 0;
      padding: 0 18px 18px;
    }}
    .source-panel details.raw {{
      margin: 0 18px 18px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #ffffff;
    }}
    article {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      margin: 14px 0;
    }}
    .translation-block {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 18px;
      margin: 0 0 14px;
    }}
    .translation-block h3 {{ margin: 0 0 8px; }}
    .translation-block ol {{ margin: 0; padding-left: 24px; }}
    .translation-block li {{ padding: 3px 0; }}
    article header {{
      display: flex; justify-content: space-between; gap: 16px; align-items: baseline;
      padding: 14px 16px; background: var(--soft); border-bottom: 1px solid var(--line);
    }}
    h3 {{ margin: 0; font-size: 1.1rem; }}
    article header p {{ margin: 0; color: var(--muted); font-size: .9rem; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    th {{ color: var(--muted); text-align: left; font-size: .82rem; text-transform: uppercase; }}
    th:first-child, td:first-child {{ width: 52px; text-align: center; color: var(--accent); font-weight: 700; }}
    td:nth-child(2), td:nth-child(3) {{ width: calc((100% - 52px) / 2); }}
    details {{ padding: 12px 16px 16px; }}
    summary {{ cursor: pointer; color: var(--accent); font-weight: 700; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; color: var(--muted); font-size: .9rem; }}
    @media (max-width: 760px) {{
      .learning-app {{ display: block; }}
      .side-rail {{
        position: sticky;
        z-index: 10;
        top: 0;
        height: auto;
        grid-template-columns: auto 1fr;
        grid-template-rows: auto;
        padding: 10px 12px;
      }}
      .chapter-rail {{ display: flex; overflow-x: auto; }}
      .chapter-rail a {{ min-width: 44px; }}
      .rail-tools {{ display: none; }}
      .lesson-workspace {{ padding: 24px 14px 48px; }}
      .lesson-header {{ grid-template-columns: 1fr; }}
      .lesson-controls {{ align-items: stretch; flex-direction: column; }}
      .scene-pager {{ justify-content: space-between; }}
      .listen-row {{ grid-template-columns: 1fr; gap: 12px; }}
      .snippet-heading {{ align-items: flex-start; }}
      .new-pill {{ display: none; }}
      article {{ overflow-x: auto; }}
      article header {{ position: sticky; left: 0; min-width: 760px; }}
      table {{ min-width: 760px; }}
      .snippet-card {{ overflow-x: visible; }}
      .snippet-card img {{ min-width: 0; }}
      .speak-btn {{ flex: 1 1 100%; }}
    }}
  </style>
</head>
<body>
  <main>
    {body}
  </main>
  <script>
    const audioCache = new Map();
    let activeAudio = null;
    let activeRecorder = null;
    let activeStream = null;
    let feedbackAudioContext = null;

    document.addEventListener("click", function (event) {{
      const button = event.target.closest("[data-speak]");
      if (!button) return;
      const text = button.getAttribute("data-speak") || "";
      const languageCode = button.getAttribute("data-lang") || "kn-IN";
      if (!text.trim()) return;
      playSarvamAudio(button, text, languageCode);
    }});

    document.addEventListener("click", function (event) {{
      const button = event.target.closest("[data-practice]");
      if (!button) return;
      const expected = button.getAttribute("data-expected") || "";
      if (!expected.trim()) return;
      recordKannadaPractice(button, expected);
    }});

    setupSceneProgress();

    async function playSarvamAudio(button, text, languageCode) {{
      const speaker = document.querySelector("[data-kannada-speaker]")?.value || "";
      const cacheKey = [languageCode, speaker, text].join("::");
      const originalHtml = button.innerHTML;
      try {{
        if (activeAudio) {{
          activeAudio.pause();
          activeAudio = null;
        }}
        button.disabled = true;
        button.textContent = "Loading...";

        let url = audioCache.get(cacheKey);
        if (!url) {{
          const response = await fetch("/api/tts", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ text, languageCode, speaker }}),
          }});
          if (!response.ok) {{
            throw new Error("Could not load audio");
          }}
          const blob = await response.blob();
          url = URL.createObjectURL(blob);
          audioCache.set(cacheKey, url);
        }}

        const audio = new Audio(url);
        activeAudio = audio;
        button.textContent = "Playing...";
        audio.onended = () => {{
          button.disabled = false;
          button.innerHTML = originalHtml;
        }};
        audio.onerror = () => {{
          button.disabled = false;
          button.innerHTML = originalHtml;
        }};
        await audio.play();
      }} catch (error) {{
        button.textContent = "Try again";
        setTimeout(() => {{
          button.disabled = false;
          button.innerHTML = originalHtml;
        }}, 1200);
      }}
    }}

    function setupSceneProgress() {{
      const cards = Array.from(document.querySelectorAll("[data-scene-card]"));
      if (!cards.length) return;
      const total = cards.length;
      const currentLabels = Array.from(document.querySelectorAll("[data-current-scene]"));
      const fill = document.querySelector("[data-progress-fill]");
      const prev = document.querySelector("[data-scene-prev]");
      const next = document.querySelector("[data-scene-next]");
      let current = 1;

      const setCurrent = (index) => {{
        current = Math.min(total, Math.max(1, index));
        currentLabels.forEach((label) => {{
          label.textContent = String(current);
        }});
        if (fill) {{
          fill.style.setProperty("--progress", ((current / total) * 100).toFixed(2) + "%");
        }}
        if (prev) prev.disabled = current <= 1;
        if (next) next.disabled = current >= total;
      }};

      const scrollToScene = (index) => {{
        const target = cards[Math.min(total, Math.max(1, index)) - 1];
        if (!target) return;
        target.scrollIntoView({{ behavior: "smooth", block: "start" }});
        setCurrent(index);
      }};

      if (prev) {{
        prev.addEventListener("click", () => scrollToScene(current - 1));
      }}
      if (next) {{
        next.addEventListener("click", () => scrollToScene(current + 1));
      }}

      if ("IntersectionObserver" in window) {{
        const observer = new IntersectionObserver((entries) => {{
          const visible = entries
            .filter((entry) => entry.isIntersecting)
            .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
          if (!visible) return;
          const index = Number(visible.target.getAttribute("data-scene-index") || "1");
          setCurrent(index);
        }}, {{ threshold: [0.28, 0.45, 0.62], rootMargin: "-18% 0px -48% 0px" }});
        cards.forEach((card) => observer.observe(card));
      }}

      setCurrent(1);
    }}

    function setPracticeFeedback(button, kind, message) {{
      const card = button.closest(".snippet-card");
      const feedback = card ? card.querySelector(".practice-feedback") : null;
      if (!feedback) return;
      feedback.className = "practice-feedback show " + kind;
      feedback.textContent = message;
      if (card) {{
        card.classList.toggle("correct", kind === "good");
        if (kind !== "good") {{
          const oldSprinkles = card.querySelector(".celebration-sprinkles");
          if (oldSprinkles) oldSprinkles.remove();
        }}
      }}
    }}

    function launchCelebration(button) {{
      const card = button.closest(".snippet-card");
      if (!card || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const oldSprinkles = card.querySelector(".celebration-sprinkles");
      if (oldSprinkles) oldSprinkles.remove();
      const colors = ["#facc15", "#22c55e", "#2dd4bf", "#3b82f6", "#f97316", "#ec4899"];
      const layer = document.createElement("div");
      layer.className = "celebration-sprinkles";
      for (let index = 0; index < 42; index += 1) {{
        const piece = document.createElement("span");
        const angle = (Math.PI * 2 * index) / 42;
        const distance = 120 + Math.random() * 210;
        piece.style.setProperty("--sprinkle-x", Math.cos(angle) * distance + "px");
        piece.style.setProperty("--sprinkle-y", Math.sin(angle) * distance - 90 + "px");
        piece.style.setProperty("--sprinkle-rotate", Math.round(Math.random() * 360) + "deg");
        piece.style.setProperty("--sprinkle-delay", Math.random() * 0.16 + "s");
        piece.style.setProperty("--sprinkle-color", colors[index % colors.length]);
        layer.appendChild(piece);
      }}
      card.appendChild(layer);
      window.setTimeout(() => layer.remove(), 1300);
    }}

    function playRetrySound() {{
      try {{
        const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextCtor) return;
        feedbackAudioContext = feedbackAudioContext || new AudioContextCtor();
        const context = feedbackAudioContext;
        const now = context.currentTime;
        const gain = context.createGain();
        gain.gain.setValueAtTime(0.0001, now);
        gain.gain.exponentialRampToValueAtTime(0.08, now + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.28);
        gain.connect(context.destination);
        [260, 190].forEach((frequency, index) => {{
          const oscillator = context.createOscillator();
          oscillator.type = "sine";
          oscillator.frequency.setValueAtTime(frequency, now + index * 0.12);
          oscillator.connect(gain);
          oscillator.start(now + index * 0.12);
          oscillator.stop(now + index * 0.12 + 0.11);
        }});
      }} catch (error) {{
        // Audio feedback is optional.
      }}
    }}

    function launchRetryFeedback(button) {{
      const card = button.closest(".snippet-card");
      if (card && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {{
        card.classList.remove("retry-shake");
        void card.offsetWidth;
        card.classList.add("retry-shake");
        window.setTimeout(() => card.classList.remove("retry-shake"), 420);
      }}
      playRetrySound();
    }}

    function preferredAudioMimeType() {{
      const types = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
      return types.find((type) => MediaRecorder.isTypeSupported(type)) || "";
    }}

    function recordingFilename(mimeType) {{
      if (mimeType.includes("webm")) return "practice.webm";
      if (mimeType.includes("mp4")) return "practice.m4a";
      if (mimeType.includes("mpeg")) return "practice.mp3";
      return "practice.webm";
    }}

    function readableApiError(result, fallback) {{
      if (!result) return fallback;
      const pickMessage = (value) => {{
        if (!value) return "";
        if (typeof value === "string") return value;
        if (typeof value.message === "string") return value.message;
        if (value.error) return pickMessage(value.error);
        try {{
          return JSON.stringify(value);
        }} catch {{
          return "";
        }}
      }};
      const rawDetail = result.detail || result.error || "";
      const detail = pickMessage(rawDetail).trim();
      if (!detail) return fallback;
      try {{
        const parsed = JSON.parse(detail);
        const parsedMessage = pickMessage(parsed);
        return parsedMessage || detail;
      }} catch {{
        return detail.length > 180 ? detail.slice(0, 177) + "..." : detail;
      }}
    }}

    async function readJsonResponse(response) {{
      const contentType = response.headers.get("content-type") || "";
      const text = await response.text();
      if (!text) return {{}};
      if (contentType.includes("application/json")) {{
        return JSON.parse(text);
      }}
      try {{
        return JSON.parse(text);
      }} catch {{
        const htmlTitle = text.match(/<title[^>]*>(.*?)<\\/title>/i);
        const nextError = text.match(/"message":"([^"]+)"/);
        const message = nextError ? nextError[1].replace(/\\\\n/g, " ") : htmlTitle ? htmlTitle[1] : "The speech check server returned an HTML error page.";
        return {{ error: message, detail: text.slice(0, 500) }};
      }}
    }}

    async function recordKannadaPractice(button, expected) {{
      const originalHtml = button.innerHTML;
      if (!navigator.mediaDevices || !window.MediaRecorder) {{
        setPracticeFeedback(button, "retry", "Microphone recording is not available in this browser.");
        return;
      }}
      if (activeRecorder && activeRecorder.state !== "inactive") {{
        activeRecorder.stop();
        return;
      }}
      try {{
        if (activeAudio) {{
          activeAudio.pause();
          activeAudio = null;
        }}
        const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
        activeStream = stream;
        const chunks = [];
        const mimeType = preferredAudioMimeType();
        const recorder = new MediaRecorder(stream, mimeType ? {{ mimeType }} : undefined);
        activeRecorder = recorder;
        button.disabled = false;
        button.textContent = "Recording... tap to stop";
        setPracticeFeedback(button, "", "Listening now. Say the Kannada phrase.");
        recorder.ondataavailable = (event) => {{
          if (event.data && event.data.size) chunks.push(event.data);
        }};
        recorder.onerror = () => {{
          setPracticeFeedback(button, "retry", "Recording failed. Please try again.");
        }};
        recorder.onstop = async () => {{
          stream.getTracks().forEach((track) => track.stop());
          activeStream = null;
          activeRecorder = null;
          button.disabled = true;
          button.textContent = "Checking...";
          try {{
            const cleanType = (mimeType || "audio/webm").split(";")[0];
            const blob = new Blob(chunks, {{ type: cleanType }});
            const form = new FormData();
            form.set("file", blob, recordingFilename(blob.type));
            form.set("expected", expected);
            const response = await fetch("/api/stt", {{ method: "POST", body: form }});
            const result = await readJsonResponse(response);
            if (!response.ok) {{
              throw new Error(readableApiError(result, "Speech check failed"));
            }}
            if (result.matched) {{
              setPracticeFeedback(button, "good", "Correct! We heard: " + (result.transcript || expected));
              button.classList.add("correct");
              button.textContent = "✓ Correct";
              launchCelebration(button);
            }} else {{
              button.classList.remove("correct");
              launchRetryFeedback(button);
              setPracticeFeedback(
                button,
                "retry",
                "Oops, try again. We heard: " + (result.transcript || "not enough audio")
              );
              button.textContent = "Try again";
            }}
          }} catch (error) {{
            const message = error instanceof Error ? error.message : "Could not check that recording.";
            launchRetryFeedback(button);
            setPracticeFeedback(button, "retry", message + " Please try again.");
            button.textContent = "Try again";
          }} finally {{
            setTimeout(() => {{
              button.disabled = false;
              if (button.textContent === "✓ Correct") {{
                return;
              }}
              button.innerHTML = originalHtml;
            }}, 1600);
          }}
        }};
        recorder.start();
        window.setTimeout(() => {{
          if (recorder.state === "recording") recorder.stop();
        }}, 4500);
      }} catch (error) {{
        if (activeStream) {{
          activeStream.getTracks().forEach((track) => track.stop());
          activeStream = null;
        }}
        activeRecorder = null;
        button.innerHTML = originalHtml;
        setPracticeFeedback(button, "retry", "Please allow microphone access and try again.");
      }}
    }}

  </script>
</body>
</html>
"""


def render_index(chapters: dict[int, list[PageConversation]]) -> str:
    cards = []
    for chapter, convs in chapters.items():
        pages = sorted({conv.page for conv in convs})
        rows = sum(len(conv.rows) for conv in convs)
        cards.append(
            f"""
            <a class="chapter-card" href="chapters/{chapter_slug(chapter)}">
              <strong>Chapter {chapter}</strong>
              <span>{html.escape(LESSON_THEMES.get(chapter, "Everyday conversation"))}</span>
              <span>{len(convs)} conversation sets · {rows} practice lines · pages {pages[0]}-{pages[-1]}</span>
            </a>
            """
        )
    body = f"""
      <h1>Spoken Kannada Conversations</h1>
      <p class="intro">Choose a chapter. Each chapter keeps the book's conversation order, adds visual practice scenes, and gives every sentence English and Kannada play buttons.</p>
      <div class="chapter-grid">{''.join(cards)}</div>
    """
    return page_shell("Spoken Kannada Conversations", body)


def render_chapter_sidebar(chapters: dict[int, list[PageConversation]], current: int) -> str:
    links = []
    for chapter in chapters:
        active = " active" if chapter == current else ""
        links.append(
            f'<a class="{active.strip()}" href="{chapter_slug(chapter)}" aria-label="Chapter {chapter}">{chapter}</a>'
        )
    return f"""
      <aside class="side-rail" aria-label="Chapter navigation">
        <a class="rail-logo" href="../conversations-page-by-page.html" aria-label="All chapters">🌷</a>
        <nav class="chapter-rail" aria-label="Chapters">
          {''.join(links)}
        </nav>
        <div class="rail-tools" aria-label="Learning tools">
          <span class="rail-tool"><span>📖</span><span>Review</span></span>
          <span class="rail-tool"><span>▥</span><span>Progress</span></span>
          <span class="rail-tool"><span>▣</span><span>Vocabulary</span></span>
          <span class="rail-tool"><span class="avatar">👦</span><span>Kid Mode</span></span>
          <span class="rail-tool"><span>?</span><span>Help</span></span>
        </div>
      </aside>
    """


def render_row_practice(item: dict, index: int, prefix: str, corrections: dict[str, dict], chapter: int) -> str:
    english = item.get("english") or "English line needs cleanup"
    original_roman = item.get("roman") or ""
    correction = with_original_deictic(
        correction_for(corrections, chapter, str(item.get("conversation", "")), int(item.get("row", 0) or 0)),
        original_roman,
    )
    practice_roman = correction.get("sarvam_roman", original_roman) if correction else original_roman
    speak_kn = correction.get("sarvam_kannada", practice_roman) if correction else practice_roman
    kannada_html = (
        f'<div class="kannada-script">{html.escape(correction["sarvam_kannada"])}</div>'
        if correction and correction.get("sarvam_kannada")
        else ""
    )
    original_html = (
        f'<div class="original-roman">Original PDF: {html.escape(original_roman)}</div>'
        if correction and original_roman and original_roman != practice_roman
        else ""
    )
    img = prefix + item.get("img", "")
    return f"""
      <article class="snippet-card" data-scene-card data-scene-index="{index}">
        <div class="snippet-body">
          <div class="snippet-heading">
            <div class="snippet-topic">
              <span class="snippet-topic-icon">👥</span>
              <h4>Conversation {html.escape(str(item.get("conversation", "")))} · {html.escape(item.get("theme_label", "Practice"))}</h4>
            </div>
            <span class="new-pill">✦ New</span>
          </div>
          <div class="snippet-line">
            <strong>{html.escape(english)}</strong>
            {kannada_html}
            <span>{html.escape(practice_roman)}</span>
          </div>
          {original_html}
          <div class="listen-row">
            <button class="speak-btn" type="button" data-lang="en-IN" data-speak="{html.escape(english)}"><span class="btn-icon">▶</span>Play English</button>
            <button class="speak-btn" type="button" data-lang="kn-IN" data-speak="{html.escape(speak_kn)}"><span class="btn-icon">▶</span>Play Kannada</button>
            <button class="speak-btn practice-btn" type="button" data-practice="kn-IN" data-expected="{html.escape(practice_roman)}"><span class="btn-icon">🎙</span>Practice Kannada</button>
          </div>
          <div class="practice-feedback" aria-live="polite"></div>
        </div>
        <img src="{html.escape(img)}" alt="{html.escape(english)}" loading="lazy" />
      </article>
    """


def render_generated_visual_practice(chapter: int, visuals: dict[str, dict], corrections: dict[str, dict], prefix: str) -> str:
    data = visuals.get(str(chapter), {})
    items = data.get("items", [])
    if not items:
        return ""
    cards = [render_row_practice(item, index, prefix, corrections, chapter) for index, item in enumerate(items, 1)]
    return f"""
      <div class="visual-practice">
        <div class="snippet-stack">{''.join(cards)}</div>
      </div>
    """


def voice_toolbar() -> str:
    return """
      <label class="voice-toolbar">
        Kannada voice
        <select data-kannada-speaker>
          <option value="priya">Priya</option>
          <option value="shubh">Shubh</option>
          <option value="aditya">Aditya</option>
          <option value="ritu">Ritu</option>
          <option value="neha">Neha</option>
          <option value="rahul">Rahul</option>
          <option value="pooja">Pooja</option>
          <option value="rohan">Rohan</option>
          <option value="kavya">Kavya</option>
          <option value="amit">Amit</option>
        </select>
        <span class="voice-wave" aria-hidden="true">⌁</span>
      </label>
    """


def render_conversation_table(conv: PageConversation, chapter: int) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row.speaker)}</td>"
        f"<td>{html.escape(row.roman)}</td>"
        f"<td>{html.escape(row.english)}</td>"
        "</tr>"
        for row in conv.rows
    )
    label = f"Conversation {conv.number}"
    return f"""
      <article>
        <header>
          <h3>Chapter {chapter} · {html.escape(label)}</h3>
          <p>{len(conv.rows)} paired lines from PDF page {conv.page}</p>
        </header>
        <table>
          <thead><tr><th>Who</th><th>Kannada from source PDF</th><th>English</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </article>
    """


def render_chapter_page(
    chapter: int,
    convs: list[PageConversation],
    chapters: dict[int, list[PageConversation]],
    visuals: dict[str, dict],
    corrections: dict[str, dict],
) -> str:
    pages = sorted({conv.page for conv in convs})
    practice = render_generated_visual_practice(chapter, visuals, corrections, "../")
    if chapter == 1 and not practice:
        practice = render_visual_practice(9, corrections, "../")
    scene_count = len(visuals.get(str(chapter), {}).get("items", [])) or (len(CHAPTER_1_VISUAL_LINES) if chapter == 1 else 0)
    scene_count = max(scene_count, 1)
    tables = "".join(render_conversation_table(conv, chapter) for conv in convs)
    raw_blocks = []
    seen_pages = set()
    for conv in convs:
        if conv.page in seen_pages:
            continue
        seen_pages.add(conv.page)
        raw_blocks.append(
            f"""
            <details class="raw">
              <summary>Raw OCR for PDF page {conv.page}</summary>
              <pre>{html.escape(chr(10).join(conv.raw_lines))}</pre>
            </details>
            """
        )
    theme = html.escape(LESSON_THEMES.get(chapter, "Everyday conversation"))
    body = f"""
      <div class="learning-app" data-scene-total="{scene_count}">
        {render_chapter_sidebar(chapters, chapter)}
        <div class="lesson-workspace">
          <header class="lesson-header">
            <div>
              <p class="lesson-kicker">Chapter {chapter}</p>
              <h1 class="lesson-title">Chapter {chapter} Visual Practice</h1>
              <p class="lesson-subtitle">{theme}. Scroll scene by scene; each image shows one sentence from this chapter.</p>
            </div>
            <div class="progress-card">
              <div class="progress-icon">📖</div>
              <div>
                <div class="progress-label"><span>Chapter Progress</span><span class="progress-count"><span data-current-scene>1</span> / {scene_count} scenes</span></div>
                <div class="progress-track"><div class="progress-fill" data-progress-fill style="--progress: {100 / scene_count:.2f}%"></div></div>
              </div>
            </div>
          </header>
          <div class="lesson-controls">
            {voice_toolbar()}
            <div class="scene-pager">
              <button class="scene-arrow prev" type="button" data-scene-prev aria-label="Previous scene">←</button>
              <span class="scene-pill">Scene <span data-current-scene>1</span> of {scene_count}</span>
              <button class="scene-arrow next" type="button" data-scene-next aria-label="Next scene">→</button>
            </div>
          </div>
          {practice}
          <div class="lesson-tip"><span>💡 <strong>Tip:</strong> Listen to each word, then try saying it out loud. Practice makes it easy!</span><span class="tip-chip">🎧 Listening Tips</span></div>
          <details class="source-panel">
            <summary>Source conversations from PDF pages {pages[0]}-{pages[-1]}</summary>
            <section>
              <h2>Source Conversations</h2>
              {tables}
            </section>
            {''.join(raw_blocks)}
          </details>
        </div>
      </div>
    """
    return page_shell(f"Chapter {chapter} · Spoken Kannada", body, "../")


def render_visual_practice(page: int, corrections: dict[str, dict], prefix: str = "") -> str:
    if page != 9:
        return ""
    cards = []
    for index, item in enumerate(CHAPTER_1_VISUAL_LINES, 1):
        note = item.get("note")
        note_html = f'<p class="grammar-note">{format_grammar_note(note)}</p>' if note else ""
        correction = with_original_deictic(
            correction_for(corrections, 1, str(item.get("conversation", "1")), int(item.get("row", index))),
            item["roman"],
        )
        english = correction.get("english", item["english"]) if correction else item["english"]
        practice_roman = correction.get("sarvam_roman", item["roman"]) if correction else item["roman"]
        speak_kn = correction.get("sarvam_kannada", item["speak_kn"]) if correction else item["speak_kn"]
        kannada_html = (
            f'<div class="kannada-script">{html.escape(correction["sarvam_kannada"])}</div>'
            if correction and correction.get("sarvam_kannada")
            else ""
        )
        original_html = (
            f'<div class="original-roman">Original PDF: {html.escape(item["roman"])}</div>'
            if correction and item["roman"] != practice_roman
            else ""
        )
        cards.append(
            f"""
              <article class="snippet-card" data-scene-card data-scene-index="{index}">
                <div class="snippet-body">
                  <div class="snippet-heading">
                    <div class="snippet-topic">
                      <span class="snippet-topic-icon">👥</span>
                      <h4>{html.escape(item['title'])}</h4>
                    </div>
                    <span class="new-pill">✦ New</span>
                  </div>
                  <div class="snippet-line">
                    <strong>{html.escape(english)}</strong>
                    {kannada_html}
                    <span>{html.escape(practice_roman)}</span>
                  </div>
                  {note_html}
                  {original_html}
                  <div class="listen-row">
                    <button class="speak-btn" type="button" data-lang="en-IN" data-speak="{html.escape(english)}"><span class="btn-icon">▶</span>Play English</button>
                    <button class="speak-btn" type="button" data-lang="kn-IN" data-speak="{html.escape(speak_kn)}"><span class="btn-icon">▶</span>Play Kannada</button>
                    <button class="speak-btn practice-btn" type="button" data-practice="kn-IN" data-expected="{html.escape(practice_roman)}"><span class="btn-icon">🎙</span>Practice Kannada</button>
                  </div>
                  <div class="practice-feedback" aria-live="polite"></div>
                </div>
                <img src="{html.escape(prefix + item['img'])}" alt="{html.escape(item['title'])}" loading="lazy" />
              </article>"""
        )
    return f"""
              <div class="visual-practice">
                <h3>Chapter 1 Visual Practice</h3>
                <p>Scroll scene by scene. Each image shows the context; tap a button to hear that exact sentence.</p>
                {voice_toolbar()}
                <div class="snippet-stack">{''.join(cards)}</div>
              </div>"""


def format_grammar_note(note: str) -> str:
    escaped = html.escape(note)
    for word in ("ivaru", "avaru"):
        escaped = re.sub(rf"\b({word})\b", r"<strong>\1</strong>", escaped, flags=re.I)
    return escaped


def main() -> None:
    conversations = extract()
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHAPTER_DIR.mkdir(parents=True, exist_ok=True)
    existing_chapter_1_visuals = {}
    if CHAPTER_VISUALS_PATH.exists():
        try:
            existing_chapter_1_visuals = json.loads(CHAPTER_VISUALS_PATH.read_text(encoding="utf-8")).get("1", {})
        except json.JSONDecodeError:
            existing_chapter_1_visuals = {}
    DATA_PATH.write_text(
        json.dumps([asdict(conversation) for conversation in conversations], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    import generate_chapter_visuals

    generate_chapter_visuals.main()
    if existing_chapter_1_visuals.get("items"):
        visuals_after_generation = load_chapter_visuals()
        visuals_after_generation["1"] = existing_chapter_1_visuals
        CHAPTER_VISUALS_PATH.write_text(
            json.dumps(visuals_after_generation, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    chapters = assign_chapters(conversations)
    visuals = load_chapter_visuals()
    corrections = load_sarvam_corrections()
    HTML_PATH.write_text(render_index(chapters), encoding="utf-8")
    for chapter, chapter_convs in chapters.items():
        path = CHAPTER_DIR / chapter_slug(chapter)
        path.write_text(render_chapter_page(chapter, chapter_convs, chapters, visuals, corrections), encoding="utf-8")
    print(f"Wrote {DATA_PATH} with {len(conversations)} page conversations")
    print(f"Wrote {HTML_PATH}")
    print(f"Wrote {len(chapters)} chapter pages to {CHAPTER_DIR}")


if __name__ == "__main__":
    main()
