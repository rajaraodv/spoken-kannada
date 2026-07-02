#!/usr/bin/env python3
"""Generate deterministic visual practice cards for each extracted lesson.

The output is intentionally simple SVG: one image per conversation row.  This
keeps every chapter split into small practice scenes without requiring manual
art direction for hundreds of sentences.
"""

from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path


DATA_PATH = Path("data/page_by_page_conversations.json")
OUT_DIR = Path("public/images/chapter-visuals")
MANIFEST_PATH = Path("data/chapter_visuals.json")

W = 1080
H = 520

THEMES = [
    ("cinema", ("movie", "cinema", "film", "theatre", "theater", "picture")),
    ("medical", ("doctor", "nurse", "medicine", "ill", "sick", "hospital", "accident", "fever", "daaktar", "narsu")),
    ("home", ("house", "home", "mother", "father", "brother", "sister", "magu", "mane", "tande", "taayi")),
    ("cafe", ("coffee", "tea", "milk", "kaafi", "ti", "haalu")),
    ("market", ("market", "shop", "price", "rupee", "beeku", "angadi", "buy", "cost")),
    ("travel", ("bus", "train", "dehli", "bangalore", "go", "come", "hoog", "band", "uur")),
    ("school", ("class", "teacher", "learn", "write", "read", "kannada", "maestru", "ood", "bare")),
    ("work", ("office", "leave", "clerk", "saar", "aafiis", "kelsa")),
    ("garden", ("garden", "tree", "water", "flower", "toota", "mara", "giDa", "niir")),
    ("food", ("breakfast", "eat", "food", "milk", "oota", "tindi", "haalu")),
    ("family", ("child", "children", "friend", "son", "daughter", "sneehit", "maga", "makka")),
]

THEME_LABELS = {
    "cinema": "At the Cinema",
    "medical": "Doctor and Health",
    "home": "At Home",
    "cafe": "Coffee and Snacks",
    "market": "Shopping and Food",
    "travel": "Going Places",
    "school": "Learning and Class",
    "work": "Office and Work",
    "garden": "Garden and Outside",
    "food": "Meals and Food",
    "family": "Family and Friends",
    "general": "Everyday Conversation",
}

PALETTE = {
    "A": "#2563eb",
    "B": "#16a34a",
    "C": "#d97706",
    "listener": "#64748b",
    "subject": "#9333ea",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def slug(value: object) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return text or "continuation"


def wrap(text: str, width: int = 38) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        if len(cur) + len(word) + 1 <= width:
            cur = f"{cur} {word}".strip()
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


def assigned_chapters(conversations: list[dict]) -> dict[int, list[dict]]:
    chapters: dict[int, list[dict]] = defaultdict(list)
    current: int | None = None
    for conv in conversations:
        if conv.get("lesson") is not None:
            current = int(conv["lesson"])
        if current is None:
            continue
        copy = dict(conv)
        copy["chapter"] = current
        chapters[current].append(copy)
    return dict(sorted(chapters.items()))


def infer_theme(rows: list[dict]) -> str:
    text = " ".join(f"{row.get('roman', '')} {row.get('english', '')}" for row in rows).lower()
    tokens = re.findall(r"[a-zA-Z]+", text)
    if {"bus", "train", "plane", "delhi", "madras", "bangalore", "market"}.intersection(tokens):
        travel_score = 2
    else:
        travel_score = 0
    best = ("general", 0)
    for theme, words in THEMES:
        score = sum(tokens.count(word) for word in words)
        if theme == "travel":
            score = travel_score + sum(tokens.count(word) for word in ("dehli", "hoog", "band", "uur"))
        if score > best[1]:
            best = (theme, score)
    return best[0]


def foreground_props(text: str) -> str:
    lower = text.lower()
    props = []
    if any(word in lower for word in ("book", "pustaka", "read", "write", "pen")):
        props.append("""
          <g filter="url(#softShadow)">
            <rect x="760" y="314" width="96" height="62" rx="8" fill="#2563eb"/>
            <path d="M808,314 V376" stroke="#bfdbfe" stroke-width="5"/>
            <text x="808" y="352" text-anchor="middle" font-size="17" font-weight="900" fill="#ffffff">BOOK</text>
          </g>
        """)
    if any(word in lower for word in ("coffee", "tea", "kaafi", "milk", "drink")):
        props.append("""
          <g filter="url(#softShadow)">
            <ellipse cx="770" cy="354" rx="58" ry="16" fill="#fff7ed" stroke="#92400e" stroke-width="3"/>
            <rect x="740" y="316" width="60" height="42" rx="12" fill="#fef3c7" stroke="#92400e" stroke-width="4"/>
            <path d="M800,326 Q830,326 820,348 Q814,362 798,354" fill="none" stroke="#92400e" stroke-width="4"/>
          </g>
        """)
    if any(word in lower for word in ("rupee", "price", "cost", "buy", "shop")):
        props.append("""
          <g filter="url(#softShadow)">
            <rect x="748" y="318" width="104" height="54" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="4"/>
            <text x="800" y="354" text-anchor="middle" font-size="28" font-weight="900" fill="#15803d">₹</text>
          </g>
        """)
    if any(word in lower for word in ("doctor", "nurse", "medicine", "ill", "sick", "fever")):
        props.append("""
          <g filter="url(#softShadow)">
            <rect x="752" y="312" width="86" height="62" rx="10" fill="#f8fafc" stroke="#ef4444" stroke-width="4"/>
            <rect x="786" y="324" width="18" height="38" fill="#ef4444"/>
            <rect x="776" y="334" width="38" height="18" fill="#ef4444"/>
          </g>
        """)
    if any(word in lower for word in ("house", "home", "mane")):
        props.append("""
          <g filter="url(#softShadow)">
            <path d="M746,326 L796,292 L846,326 Z" fill="#dc2626"/>
            <rect x="758" y="326" width="76" height="50" rx="6" fill="#fde68a" stroke="#d97706" stroke-width="3"/>
            <rect x="788" y="348" width="18" height="28" fill="#92400e"/>
          </g>
        """)
    return "".join(props)


def person_svg(cx: int, base_y: int, shirt: str, name: str, scale: float = 1.0, pose: str = "neutral") -> str:
    head = 32 * scale
    body_h = 86 * scale
    body_w = 82 * scale
    skin = "#f2c28b"
    hair = "#22223a"
    head_y = base_y - body_h - head
    arm_left = (
        f'<line x1="{cx-body_w*.34:.1f}" y1="{base_y-body_h+18*scale:.1f}" x2="{cx-body_w*.74:.1f}" y2="{base_y-body_h+4*scale:.1f}" stroke="{shirt}" stroke-width="{12*scale:.1f}" stroke-linecap="round"/>'
        if pose == "wave"
        else f'<line x1="{cx-body_w*.34:.1f}" y1="{base_y-body_h+18*scale:.1f}" x2="{cx-body_w*.68:.1f}" y2="{base_y-body_h+38*scale:.1f}" stroke="{shirt}" stroke-width="{12*scale:.1f}" stroke-linecap="round"/>'
    )
    arm_right = (
        f'<line x1="{cx+body_w*.34:.1f}" y1="{base_y-body_h+18*scale:.1f}" x2="{cx+body_w*.92:.1f}" y2="{base_y-body_h+20*scale:.1f}" stroke="{shirt}" stroke-width="{12*scale:.1f}" stroke-linecap="round"/><circle cx="{cx+body_w*.98:.1f}" cy="{base_y-body_h+20*scale:.1f}" r="{6*scale:.1f}" fill="{skin}"/>'
        if pose == "point"
        else f'<line x1="{cx+body_w*.34:.1f}" y1="{base_y-body_h+18*scale:.1f}" x2="{cx+body_w*.68:.1f}" y2="{base_y-body_h+38*scale:.1f}" stroke="{shirt}" stroke-width="{12*scale:.1f}" stroke-linecap="round"/>'
    )
    return f"""
      <ellipse cx="{cx}" cy="{base_y+12}" rx="{body_w*.48:.1f}" ry="10" fill="#00000018"/>
      <rect x="{cx-18*scale:.1f}" y="{base_y-body_h+52*scale:.1f}" width="{13*scale:.1f}" height="{58*scale:.1f}" rx="6" fill="#374151"/>
      <rect x="{cx+6*scale:.1f}" y="{base_y-body_h+52*scale:.1f}" width="{13*scale:.1f}" height="{58*scale:.1f}" rx="6" fill="#374151"/>
      <path d="M{cx-body_w/2:.1f},{base_y-24*scale:.1f} Q{cx},{base_y-body_h-10*scale:.1f} {cx+body_w/2:.1f},{base_y-24*scale:.1f} Z" fill="{shirt}"/>
      <rect x="{cx-7*scale:.1f}" y="{head_y+head-3*scale:.1f}" width="{14*scale:.1f}" height="{20*scale:.1f}" fill="{skin}"/>
      {arm_left}
      {arm_right}
      <circle cx="{cx}" cy="{head_y}" r="{head:.1f}" fill="{skin}" stroke="#00000020"/>
      <path d="M{cx-head:.1f},{head_y-3*scale:.1f} Q{cx-head*.7:.1f},{head_y-head*1.05:.1f} {cx},{head_y-head*.95:.1f} Q{cx+head*.8:.1f},{head_y-head*.95:.1f} {cx+head:.1f},{head_y-3*scale:.1f} Q{cx},{head_y-head*.25:.1f} {cx-head:.1f},{head_y-3*scale:.1f} Z" fill="{hair}"/>
      <circle cx="{cx-10*scale:.1f}" cy="{head_y-2*scale:.1f}" r="{3.2*scale:.1f}" fill="#1f2937"/>
      <circle cx="{cx+10*scale:.1f}" cy="{head_y-2*scale:.1f}" r="{3.2*scale:.1f}" fill="#1f2937"/>
      <path d="M{cx-11*scale:.1f},{head_y+13*scale:.1f} Q{cx},{head_y+23*scale:.1f} {cx+11*scale:.1f},{head_y+13*scale:.1f}" fill="none" stroke="#7c2d12" stroke-width="{2.5*scale:.1f}" stroke-linecap="round"/>
      <rect x="{cx-48*scale:.1f}" y="{base_y+22}" rx="10" width="{96*scale:.1f}" height="{26*scale:.1f}" fill="{shirt}"/>
      <text x="{cx}" y="{base_y+40}" text-anchor="middle" font-size="{15*scale:.1f}" font-weight="800" fill="white">{esc(name)}</text>
    """


def defs_svg(theme: str) -> str:
    return f"""
      <defs>
        <linearGradient id="sky-general" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stop-color="#dff3ff"/>
          <stop offset="1" stop-color="#fff7ed"/>
        </linearGradient>
        <linearGradient id="floor-general" x1="0" x2="1">
          <stop offset="0" stop-color="#f5e9d4"/>
          <stop offset="1" stop-color="#e8d6b7"/>
        </linearGradient>
        <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#1f2937" flood-opacity=".18"/>
        </filter>
      </defs>
    """


def room_base(accent: str = "#f59e0b") -> str:
    return f"""
      <rect x="24" y="22" width="{W-48}" height="{H-44}" rx="26" fill="url(#sky-general)" stroke="#ead8bd" stroke-width="4"/>
      <path d="M44,322 H1036 V478 H44 Z" fill="url(#floor-general)"/>
      <path d="M44,322 H1036" stroke="#d7bea0" stroke-width="4"/>
      <circle cx="945" cy="86" r="38" fill="{accent}" opacity=".18"/>
    """


def background_svg(theme: str, text: str = "") -> str:
    lower = text.lower()
    if theme == "home":
        return room_base("#ef4444") + """
          <rect x="718" y="114" width="246" height="166" rx="12" fill="#fde68a" stroke="#d6a85b" stroke-width="3" filter="url(#softShadow)"/>
          <path d="M698,126 L842,42 L986,126 Z" fill="#dc2626"/>
          <rect x="825" y="204" width="48" height="76" rx="4" fill="#92400e"/>
          <rect x="742" y="152" width="48" height="42" fill="#bfdbfe"/><rect x="900" y="152" width="40" height="42" fill="#bfdbfe"/>
          <rect x="720" y="330" width="220" height="48" rx="24" fill="#fca5a5"/>
          <rect x="750" y="292" width="40" height="72" fill="#7c2d12"/>
        """
    if theme == "cinema":
        return room_base("#7c3aed") + """
          <rect x="664" y="78" width="332" height="210" rx="18" fill="#1f2937" filter="url(#softShadow)"/>
          <rect x="690" y="106" width="280" height="130" rx="10" fill="#fde68a"/>
          <text x="830" y="182" text-anchor="middle" font-size="34" font-weight="900" fill="#7c2d12">MOVIE</text>
          <rect x="690" y="250" width="280" height="18" fill="#dc2626"/>
          <g fill="#ef4444"><rect x="704" y="300" width="32" height="56"/><rect x="754" y="300" width="32" height="56"/><rect x="804" y="300" width="32" height="56"/><rect x="854" y="300" width="32" height="56"/><rect x="904" y="300" width="32" height="56"/></g>
        """
    if theme == "market":
        return room_base("#f97316") + """
          <rect x="690" y="96" width="284" height="190" rx="12" fill="#e0f2fe" stroke="#0ea5e9" stroke-width="3" filter="url(#softShadow)"/>
          <rect x="690" y="96" width="284" height="46" rx="12" fill="#f97316"/>
          <text x="832" y="128" text-anchor="middle" font-size="22" font-weight="900" fill="white">ANGADI</text>
          <g fill="#22c55e"><circle cx="738" cy="202" r="20"/><circle cx="792" cy="202" r="20"/><circle cx="846" cy="202" r="20"/></g>
          <g fill="#facc15"><rect x="716" y="238" width="52" height="28" rx="6"/><rect x="790" y="238" width="52" height="28" rx="6"/><rect x="864" y="238" width="52" height="28" rx="6"/></g>
        """
    if theme == "cafe":
        return room_base("#a16207") + """
          <rect x="706" y="248" width="246" height="28" rx="14" fill="#8b5e34"/>
          <rect x="736" y="276" width="18" height="76" fill="#8b5e34"/><rect x="904" y="276" width="18" height="76" fill="#8b5e34"/>
          <ellipse cx="790" cy="222" rx="46" ry="18" fill="#fff7ed" stroke="#92400e" stroke-width="4"/>
          <rect x="760" y="182" width="60" height="44" rx="12" fill="#fef3c7" stroke="#92400e" stroke-width="4"/>
          <path d="M820,194 Q854,194 844,216 Q838,232 818,222" fill="none" stroke="#92400e" stroke-width="5"/>
          <path d="M764,160 Q786,136 806,160" fill="none" stroke="#94a3b8" stroke-width="4" stroke-linecap="round"/>
          <text x="880" y="208" text-anchor="middle" font-size="28" font-weight="900" fill="#7c2d12">CAFE</text>
        """
    if theme == "travel":
        vehicle = "TRAIN" if "train" in lower else "BUS"
        return room_base("#0284c7") + f"""
          <path d="M652,286 C744,232 880,232 994,286" fill="none" stroke="#94a3b8" stroke-width="8"/>
          <rect x="676" y="146" width="304" height="108" rx="26" fill="#bae6fd" stroke="#0284c7" stroke-width="4" filter="url(#softShadow)"/>
          <g fill="#e0f2fe"><rect x="714" y="170" width="50" height="36" rx="6"/><rect x="786" y="170" width="50" height="36" rx="6"/><rect x="858" y="170" width="50" height="36" rx="6"/></g>
          <circle cx="744" cy="264" r="22" fill="#1f2937"/><circle cx="912" cy="264" r="22" fill="#1f2937"/>
          <text x="828" y="234" text-anchor="middle" font-size="28" font-weight="900" fill="#0369a1">{vehicle}</text>
          <rect x="705" y="310" width="228" height="46" rx="8" fill="#fef3c7" stroke="#d97706"/>
          <text x="819" y="340" text-anchor="middle" font-size="18" font-weight="900" fill="#92400e">TICKET COUNTER</text>
        """
    if theme == "school":
        return room_base("#16a34a") + """
          <rect x="688" y="82" width="292" height="170" rx="10" fill="#14532d" stroke="#7c2d12" stroke-width="8" filter="url(#softShadow)"/>
          <text x="834" y="146" text-anchor="middle" font-size="30" font-weight="900" fill="#dcfce7">ಕನ್ನಡ</text>
          <text x="834" y="190" text-anchor="middle" font-size="24" font-weight="900" fill="#dcfce7">ABC 123</text>
          <line x1="716" y1="214" x2="952" y2="214" stroke="#dcfce7" stroke-width="4"/>
          <rect x="732" y="290" width="210" height="56" rx="8" fill="#fef3c7" stroke="#d97706"/>
          <g fill="#2563eb"><rect x="750" y="305" width="36" height="24" rx="3"/><rect x="806" y="305" width="36" height="24" rx="3"/><rect x="862" y="305" width="36" height="24" rx="3"/></g>
        """
    if theme == "work":
        return room_base("#64748b") + """
          <rect x="706" y="66" width="250" height="230" rx="10" fill="#e5e7eb" stroke="#94a3b8" stroke-width="4" filter="url(#softShadow)"/>
          <text x="831" y="98" text-anchor="middle" font-size="22" font-weight="900" fill="#475569">OFFICE</text>
          <g fill="#93c5fd"><rect x="736" y="120" width="42" height="38" rx="4"/><rect x="808" y="120" width="42" height="38" rx="4"/><rect x="880" y="120" width="42" height="38" rx="4"/><rect x="736" y="180" width="42" height="38" rx="4"/><rect x="808" y="180" width="42" height="38" rx="4"/><rect x="880" y="180" width="42" height="38" rx="4"/></g>
          <rect x="760" y="316" width="170" height="54" rx="8" fill="#7c2d12"/><rect x="778" y="332" width="134" height="10" fill="#fef3c7"/>
        """
    if theme == "garden":
        return room_base("#22c55e") + """
          <path d="M650,330 C750,272 890,292 1005,330 V478 H650 Z" fill="#bbf7d0"/>
          <rect x="816" y="130" width="32" height="160" rx="10" fill="#92400e"/>
          <circle cx="832" cy="104" r="66" fill="#22c55e"/><circle cx="884" cy="140" r="46" fill="#16a34a"/><circle cx="778" cy="142" r="44" fill="#4ade80"/>
          <g fill="#ef4444"><circle cx="728" cy="306" r="8"/><circle cx="778" cy="294" r="8"/><circle cx="928" cy="300" r="8"/></g>
          <path d="M704,350 Q840,302 980,352" fill="none" stroke="#15803d" stroke-width="6"/>
        """
    if theme == "food":
        return room_base("#d97706") + """
          <rect x="700" y="260" width="284" height="32" rx="16" fill="#8b5e34"/>
          <ellipse cx="820" cy="220" rx="112" ry="34" fill="#fef3c7" stroke="#d97706" stroke-width="4"/>
          <circle cx="780" cy="210" r="24" fill="#ef4444"/><circle cx="834" cy="210" r="24" fill="#22c55e"/><circle cx="888" cy="210" r="24" fill="#facc15"/>
          <rect x="744" y="292" width="20" height="78" fill="#8b5e34"/><rect x="920" y="292" width="20" height="78" fill="#8b5e34"/>
          <text x="830" y="150" text-anchor="middle" font-size="24" font-weight="900" fill="#92400e">TIFFIN</text>
        """
    if theme == "medical":
        return room_base("#ef4444") + """
          <rect x="704" y="90" width="268" height="186" rx="16" fill="#f8fafc" stroke="#94a3b8" stroke-width="4" filter="url(#softShadow)"/>
          <rect x="810" y="126" width="44" height="116" fill="#ef4444"/><rect x="774" y="162" width="116" height="44" fill="#ef4444"/>
          <rect x="706" y="318" width="260" height="48" rx="10" fill="#dbeafe" stroke="#60a5fa"/>
          <text x="836" y="350" text-anchor="middle" font-size="20" font-weight="900" fill="#1d4ed8">CLINIC</text>
        """
    return room_base("#f59e0b") + """
      <circle cx="850" cy="150" r="86" fill="#fef3c7" stroke="#f59e0b" opacity=".85"/>
      <path d="M790,250 Q850,210 910,250" fill="none" stroke="#f59e0b" stroke-width="8" stroke-linecap="round"/>
      <rect x="724" y="290" width="240" height="64" rx="12" fill="#e0f2fe" stroke="#38bdf8"/>
      <text x="844" y="330" text-anchor="middle" font-size="20" font-weight="900" fill="#0369a1">EVERYDAY</text>
    """


def scene_svg(chapter: int, conv_number: str, row_index: int, row: dict, theme: str) -> str:
    english = row.get("english") or "English line needs cleanup"
    roman = row.get("roman") or ""
    speaker = row.get("speaker") or "A"
    accent = {"A": PALETTE["A"], "B": PALETTE["B"], "C": PALETTE["C"]}.get(speaker, "#0f766e")
    title = f"Chapter {chapter} · Conversation {conv_number}"
    en_lines = wrap(english, 44)
    kn_lines = wrap(roman, 44)
    text_lines = en_lines + kn_lines
    bubble_h = 94 + max(0, len(text_lines) - 2) * 28
    text_parts = []
    y = 90
    for line in en_lines:
        text_parts.append(f'<text x="78" y="{y}" font-size="28" font-weight="800" fill="#1f2937">{esc(line)}</text>')
        y += 34
    for line in kn_lines:
        text_parts.append(f'<text x="78" y="{y}" font-size="27" font-style="italic" font-weight="800" fill="{accent}">{esc(line)}</text>')
        y += 34
    scene_text = f"{english} {roman}"
    subject_far = bool(re.search(r"\b(that|there|his|her|she|he)\b", english.lower())) or roman.lower().startswith(("avaru", "avara", "adu"))
    subject_near = bool(re.search(r"\b(this|here)\b", english.lower())) or roman.lower().startswith(("ivaru", "ivara", "idu", "idara"))
    listener_x = 468 if not subject_near else 430
    subject_x = 890 if subject_far else 650
    subject_scale = 0.72 if subject_far else 0.92
    subject_opacity = ".92" if subject_far else "1"
    subject_label = "That person" if subject_far else "This person"
    subject_svg = ""
    pointer_svg = ""
    if subject_far or subject_near:
        subject_svg = f'<g opacity="{subject_opacity}">{person_svg(subject_x, 382, PALETTE["subject"], subject_label, subject_scale)}</g>'
        pointer_svg = (
            f'<path d="M258,266 Q{(258+subject_x)/2:.1f},210 {subject_x-34*subject_scale:.1f},286" '
            f'fill="none" stroke="{accent}" stroke-width="5" stroke-dasharray="8 10" stroke-linecap="round"/>'
            f'<circle cx="{subject_x-34*subject_scale:.1f}" cy="286" r="7" fill="{accent}"/>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Verdana,Arial,sans-serif">
      {defs_svg(theme)}
      <rect width="{W}" height="{H}" fill="#fffdf8"/>
      {background_svg(theme, scene_text)}
      <text x="54" y="52" font-size="18" font-weight="800" fill="#92400e">{esc(title)}</text>
      <text x="1026" y="52" text-anchor="end" font-size="18" font-weight="800" fill="#64748b">{esc(THEME_LABELS[theme])}</text>
      <rect x="54" y="64" width="570" height="{bubble_h}" rx="22" fill="#ffffff" stroke="{accent}" stroke-width="4" filter="url(#softShadow)"/>
      <rect x="70" y="78" width="538" height="{max(34, bubble_h-28)}" rx="16" fill="#f8fafc" opacity=".72"/>
      <path d="M190,{64+bubble_h} L232,{64+bubble_h} L204,322 Z" fill="#ffffff" stroke="{accent}" stroke-width="4"/>
      <rect x="188" y="{60+bubble_h}" width="48" height="10" fill="#ffffff"/>
      {''.join(text_parts)}
      {foreground_props(scene_text)}
      {pointer_svg}
      <line x1="74" y1="390" x2="1006" y2="390" stroke="#d8c7ae" stroke-width="4"/>
      {person_svg(205, 382, accent, f"Speaker {esc(speaker)}", 1.05, "point" if (subject_far or subject_near) else "wave")}
      {person_svg(listener_x, 382, PALETTE["listener"], "Listener", .96)}
      {subject_svg}
    </svg>"""


def main() -> None:
    conversations = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    chapters = assigned_chapters(conversations)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}
    for chapter, convs in chapters.items():
        chapter_dir = OUT_DIR / f"chapter-{chapter:02d}"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        chapter_rows = [row for conv in convs for row in conv["rows"]]
        chapter_theme = infer_theme(chapter_rows)
        manifest[str(chapter)] = {
            "theme": chapter_theme,
            "theme_label": THEME_LABELS[chapter_theme],
            "items": [],
        }
        for conv in convs:
            conv_theme = infer_theme(conv["rows"]) or chapter_theme
            conv_number = str(conv["number"])
            for row_index, row in enumerate(conv["rows"], 1):
                row_theme = infer_theme([row])
                if row_theme == "general":
                    row_theme = conv_theme
                filename = f"conversation-{slug(conv_number)}-{row_index:02d}.svg"
                rel = f"images/chapter-visuals/chapter-{chapter:02d}/{filename}"
                (chapter_dir / filename).write_text(
                    scene_svg(chapter, conv_number, row_index, row, row_theme),
                    encoding="utf-8",
                )
                manifest[str(chapter)]["items"].append(
                    {
                        "conversation": conv_number,
                        "row": row_index,
                        "img": rel,
                        "theme": row_theme,
                        "theme_label": THEME_LABELS[row_theme],
                        "speaker": row.get("speaker", ""),
                        "english": row.get("english", ""),
                        "roman": row.get("roman", ""),
                    }
                )
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote visuals for {len(chapters)} chapters to {OUT_DIR}")
    print(f"Wrote {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
