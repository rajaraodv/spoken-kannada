#!/usr/bin/env python3
"""Generate a kid-friendly cartoon comic strip for Lesson 1.

Scene-based with roles, so the staging matches the meaning:
  - speaker  : the one talking (gets the speech bubble)
  - listener : the person being spoken TO (stands next to the speaker)
  - subject  : the third person being talked ABOUT (stands apart, highlighted,
               with a pointing arrow arcing over to them)
So "Who is she?" shows Raju asking Shekhar (both on the left) about Sheela (right).

English on top of each speech bubble, romanized Kannada underneath.
Reads dialogue text from data/pages_raw/page-009.json so wording stays in sync.
Output: public/images/chapter-1-meeting-people-cartoon.{svg,png}

Run: python3 scripts/generate_comic.py
"""

from __future__ import annotations

import json
from pathlib import Path

SRC = Path("data/pages_raw/page-009.json")
OUT = Path("public/images/chapter-1-meeting-people-cartoon")

W = 1080
PAD = 26

# skin, hair, shirt, accent, female, glasses, child
PEOPLE = {
    "Raju":    dict(skin="#f1c27d", hair="#2b2118", shirt="#2563eb", accent="#2563eb", glasses=True),
    "Shekhar": dict(skin="#e0ac69", hair="#1f2937", shirt="#16a34a", accent="#16a34a"),
    "Mohan":   dict(skin="#f1c27d", hair="#4b2e2e", shirt="#f59e0b", accent="#d97706"),
    "Sheela":  dict(skin="#f5cda0", hair="#3a2a1a", shirt="#a855f7", accent="#9333ea", female=True),
    "Shankar": dict(skin="#d99a5b", hair="#111827", shirt="#ef4444", accent="#dc2626"),
    "Lalita":  dict(skin="#f3c9a0", hair="#231a12", shirt="#ec4899", accent="#db2777", female=True),
    "Kiran":   dict(skin="#f5cda0", hair="#2b2118", shirt="#06b6d4", accent="#0891b2", child=True),
    "Father":  dict(skin="#e0ac69", hair="#6b7280", shirt="#0f766e", accent="#0f766e"),
}

CAST = ["Raju", "Mohan", "Shekhar", "Sheela", "Shankar"]

HEADR = 25
TORSO = 58
LEG = 40
BODYW = 66


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- characters
def head_and_face(cx, head_cy, p):
    skin, hair = p["skin"], p["hair"]
    parts = []
    if p.get("female"):
        parts.append(f'<circle cx="{cx}" cy="{head_cy}" r="{HEADR+6}" fill="{hair}"/>')
    parts.append(f'<circle cx="{cx}" cy="{head_cy}" r="{HEADR}" fill="{skin}" stroke="#00000022"/>')
    parts.append(
        f'<path d="M{cx-HEADR},{head_cy-2} '
        f'Q{cx-HEADR},{head_cy-HEADR-10} {cx},{head_cy-HEADR-8} '
        f'Q{cx+HEADR},{head_cy-HEADR-10} {cx+HEADR},{head_cy-2} '
        f'Q{cx},{head_cy-HEADR+7} {cx-HEADR},{head_cy-2} Z" fill="{hair}"/>'
    )
    ey = head_cy - 2
    parts.append(f'<circle cx="{cx-9}" cy="{ey}" r="3" fill="#1f2937"/>')
    parts.append(f'<circle cx="{cx+9}" cy="{ey}" r="3" fill="#1f2937"/>')
    if p.get("glasses"):
        parts.append(f'<circle cx="{cx-9}" cy="{ey}" r="7" fill="none" stroke="#1f2937" stroke-width="1.6"/>')
        parts.append(f'<circle cx="{cx+9}" cy="{ey}" r="7" fill="none" stroke="#1f2937" stroke-width="1.6"/>')
        parts.append(f'<line x1="{cx-2}" y1="{ey}" x2="{cx+2}" y2="{ey}" stroke="#1f2937" stroke-width="1.6"/>')
    parts.append(
        f'<path d="M{cx-9},{head_cy+10} Q{cx},{head_cy+18} {cx+9},{head_cy+10}" '
        f'fill="none" stroke="#7c2d12" stroke-width="2" stroke-linecap="round"/>'
    )
    return "".join(parts)


def draw_person(cx, head_cy, p, pose="neutral", direction=1):
    """pose: neutral|wave|self|point. Returns (svg, info)."""
    s = 0.82 if p.get("child") else 1.0
    headr = HEADR * s
    torso = TORSO * s
    leg = LEG * s
    bodyw = BODYW * s

    torso_top = head_cy + headr + 4
    hip_y = torso_top + torso
    feet_y = hip_y + leg
    shoulder_y = torso_top + 12
    skin, shirt = p["skin"], p["shirt"]

    parts = [f'<ellipse cx="{cx}" cy="{feet_y+6}" rx="{bodyw*0.55}" ry="7" fill="#00000018"/>']
    parts.append(f'<rect x="{cx-14*s}" y="{hip_y-6}" width="{11*s}" height="{leg+6}" rx="5" fill="#374151"/>')
    parts.append(f'<rect x="{cx+3*s}" y="{hip_y-6}" width="{11*s}" height="{leg+6}" rx="5" fill="#374151"/>')
    parts.append(f'<ellipse cx="{cx-8*s}" cy="{feet_y+2}" rx="{9*s}" ry="5" fill="#1f2937"/>')
    parts.append(f'<ellipse cx="{cx+8*s}" cy="{feet_y+2}" rx="{9*s}" ry="5" fill="#1f2937"/>')
    parts.append(
        f'<path d="M{cx-bodyw/2},{hip_y} L{cx-bodyw/2+4},{torso_top+6} '
        f'Q{cx},{torso_top-6} {cx+bodyw/2-4},{torso_top+6} L{cx+bodyw/2},{hip_y} Z" fill="{shirt}"/>'
    )
    parts.append(f'<rect x="{cx-6*s}" y="{torso_top-8}" width="{12*s}" height="12" fill="{skin}"/>')

    def arm(x1, y1, x2, y2, hand=True, finger_dir=0):
        a = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{shirt}" '
             f'stroke-width="{12*s}" stroke-linecap="round"/>')
        if hand:
            a += f'<circle cx="{x2}" cy="{y2}" r="{7*s}" fill="{skin}"/>'
        if finger_dir:
            a += (f'<line x1="{x2}" y1="{y2}" x2="{x2+finger_dir*12*s}" y2="{y2}" '
                  f'stroke="{skin}" stroke-width="{5*s}" stroke-linecap="round"/>')
        return a

    info = {"cx": cx, "head_top": head_cy - headr, "head_cy": head_cy, "hand": None}
    rest_dir = -direction
    parts.append(arm(cx + rest_dir * bodyw * 0.38, shoulder_y,
                     cx + rest_dir * bodyw * 0.5, hip_y - 8))

    if pose == "wave":
        parts.append(arm(cx + direction * bodyw * 0.38, shoulder_y,
                         cx + direction * (bodyw * 0.5 + 14), torso_top - 24))
    elif pose == "self":
        parts.append(arm(cx + direction * bodyw * 0.4, shoulder_y,
                         cx + direction * 4, torso_top + 22, finger_dir=-direction))
    elif pose == "point":
        hx, hy = cx + direction * (bodyw * 0.5 + 34), shoulder_y - 6
        parts.append(arm(cx + direction * bodyw * 0.38, shoulder_y, hx, hy, finger_dir=direction))
        info["hand"] = (hx + direction * 12 * s, hy)
    else:
        parts.append(arm(cx + direction * bodyw * 0.38, shoulder_y,
                         cx + direction * bodyw * 0.5, hip_y - 8))

    parts.append(head_and_face(cx, head_cy, p))
    return "".join(parts), info


def name_tag(cx, y, name, accent):
    w = max(56, len(name) * 9 + 18)
    return (
        f'<rect x="{cx-w/2}" y="{y}" rx="9" width="{w}" height="22" fill="{accent}"/>'
        f'<text x="{cx}" y="{y+15.5}" text-anchor="middle" font-size="13" '
        f'font-weight="700" fill="#ffffff">{esc(name)}</text>'
    )


# ---------------------------------------------------------------- bubbles
def wrap(text, max_chars):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


LINE_H = 21


def measure_bubble(pairs, w):
    cpl = int((w - 36) / 8.4)
    n = sum(len(wrap(en, cpl)) + len(wrap(kn, cpl)) for en, kn in pairs)
    n += (len(pairs) - 1)
    return 16 + n * LINE_H + 14


def draw_bubble(x, y, w, pairs, accent, tail_x, tail_to_y):
    h = measure_bubble(pairs, w)
    cpl = int((w - 36) / 8.4)
    parts = [
        f'<rect x="{x}" y="{y}" rx="16" width="{w}" height="{h}" fill="#ffffff" '
        f'stroke="{accent}" stroke-width="2.5"/>'
    ]
    txc = min(max(tail_x, x + 24), x + w - 24)
    parts.append(
        f'<path d="M{txc-11},{y+h} L{txc+11},{y+h} L{txc+2},{tail_to_y} Z" '
        f'fill="#ffffff" stroke="{accent}" stroke-width="2.5"/>'
    )
    parts.append(f'<rect x="{txc-9}" y="{y+h-4}" width="22" height="6" fill="#ffffff"/>')
    ty = y + 22
    for i, (en, kn) in enumerate(pairs):
        for ln in wrap(en, cpl):
            parts.append(f'<text x="{x+18}" y="{ty}" font-size="16" font-weight="700" '
                         f'fill="#1f2937">{esc(ln)}</text>')
            ty += LINE_H
        for ln in wrap(kn, cpl):
            parts.append(f'<text x="{x+18}" y="{ty}" font-size="16" font-style="italic" '
                         f'font-weight="600" fill="{accent}">{esc(ln)}</text>')
            ty += LINE_H
        if i < len(pairs) - 1:
            parts.append(f'<line x1="{x+16}" y1="{ty-12}" x2="{x+w-16}" y2="{ty-12}" '
                         f'stroke="#eee" stroke-width="1"/>')
            ty += LINE_H - 6
    return "".join(parts), h


def pointer_curve(x1, y1, x2, y2, color):
    mx, my = (x1 + x2) / 2, min(y1, y2) - 55
    return (
        f'<path d="M{x1},{y1} Q{mx},{my} {x2},{y2}" fill="none" stroke="{color}" '
        f'stroke-width="3" stroke-dasharray="2 8" stroke-linecap="round"/>'
        f'<circle cx="{x2}" cy="{y2}" r="4.5" fill="{color}"/>'
    )


# ---------------------------------------------------------------- panels
def render_panel(panel_x, panel_w, y0, chars, bubbles):
    subjects = [c for c in chars if c.get("role") == "subject"]
    nonsub = [c for c in chars if c.get("role") != "subject"]

    bub_w = 470 if len(bubbles) == 1 else min(380, (panel_w - 60) / len(bubbles))
    bub_zone = max(measure_bubble(b["pairs"], bub_w) for b in bubbles) + 24

    head_top = y0 + 14 + bub_zone
    head_cy = head_top + HEADR
    ground_y = head_cy + HEADR + TORSO + LEG
    panel_h = (ground_y + 36) - y0
    center = panel_x + panel_w / 2

    # ----- x positions by role -----
    name_to_x = {}
    if subjects:
        left_fx = [0.25] if len(nonsub) <= 1 else [0.14, 0.33]
        for c, fx in zip(nonsub, left_fx):
            name_to_x[c["name"]] = panel_x + panel_w * fx
        subject_fx = []
        for i, c in enumerate(subjects):
            if c.get("distance") == "near":
                subject_fx.append(0.53 + i * 0.15)
            else:
                subject_fx.append(0.86 + i * 0.08)
        for c, fx in zip(subjects, subject_fx):
            name_to_x[c["name"]] = panel_x + panel_w * fx
    elif len(nonsub) == 1:
        name_to_x[nonsub[0]["name"]] = center
    else:
        for c, fx in zip(nonsub, [0.27, 0.73]):
            name_to_x[c["name"]] = panel_x + panel_w * fx

    inner = [
        f'<rect x="{panel_x}" y="{y0}" rx="16" width="{panel_w}" height="{panel_h}" '
        f'fill="#e8f6ff" stroke="#e7d3ba" stroke-width="2"/>',
        f'<rect x="{panel_x+2}" y="{ground_y-52}" width="{panel_w-4}" height="{panel_h-(ground_y-y0)+50}" '
        f'fill="#f1dfc1" opacity="0.75"/>',
        f'<rect x="{panel_x+panel_w-170}" y="{y0+32}" width="92" height="64" rx="8" fill="#bfdbfe" '
        f'stroke="#60a5fa" stroke-width="2" opacity="0.75"/>',
        f'<line x1="{panel_x+panel_w-124}" y1="{y0+32}" x2="{panel_x+panel_w-124}" y2="{y0+96}" '
        f'stroke="#60a5fa" stroke-width="2" opacity="0.75"/>',
        f'<line x1="{panel_x+panel_w-170}" y1="{y0+64}" x2="{panel_x+panel_w-78}" y2="{y0+64}" '
        f'stroke="#60a5fa" stroke-width="2" opacity="0.75"/>',
        f'<circle cx="{panel_x+panel_w-36}" cy="{y0+42}" r="22" fill="#fde68a" opacity="0.55"/>',
        f'<ellipse cx="{panel_x+panel_w-118}" cy="{ground_y+4}" rx="82" ry="20" fill="#fca5a5" opacity="0.45"/>',
        f'<line x1="{panel_x+18}" y1="{ground_y+8}" x2="{panel_x+panel_w-18}" '
        f'y2="{ground_y+8}" stroke="#eaddcb" stroke-width="2"/>',
    ]

    # highlight subjects (behind people)
    for c in subjects:
        tx = name_to_x[c["name"]]
        inner.append(f'<circle cx="{tx}" cy="{head_cy}" r="{HEADR+14}" fill="#fde68a" opacity="0.7"/>')

    # draw people
    infos = {}
    for c in chars:
        name = c["name"]
        x = name_to_x[name]
        p = PEOPLE[name]
        if c.get("role") == "speaker":
            if subjects:
                pose, direction = "point", 1
            elif len(nonsub) > 1:
                pose, direction = "wave", (1 if x < center else -1)
            else:
                pose, direction = "self", 1
        else:
            pose, direction = "neutral", (1 if x <= center else -1)
        svg, info = draw_person(x, head_cy, p, pose, direction)
        inner.append(svg)
        inner.append(name_tag(x, ground_y + 12, name, p["accent"]))
        infos[name] = info

    # pointing arrows: each speaker -> the subject
    if subjects:
        tgt = infos[subjects[0]["name"]]
        for c in chars:
            if c.get("role") == "speaker" and infos[c["name"]]["hand"]:
                hand = infos[c["name"]]["hand"]
                inner.append(pointer_curve(hand[0], hand[1], tgt["cx"],
                                           tgt["head_cy"] - HEADR - 6, PEOPLE[c["name"]]["accent"]))

    # bubbles above their speakers
    for b in bubbles:
        sx = name_to_x.get(b["by"], center)
        bx = min(max(sx - bub_w / 2, panel_x + 16), panel_x + panel_w - bub_w - 16)
        svg, _ = draw_bubble(bx, y0 + 14, bub_w, b["pairs"],
                             PEOPLE[b["by"]]["accent"], sx, infos[b["by"]]["head_top"] - 2)
        inner.append(svg)

    return "".join(inner), panel_h


# ---------------------------------------------------------------- script
def build():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    convs = {c["number"]: c["rows"] for c in data["blocks"] if c.get("type") == "conversation"}

    def P(conv, idx):
        r = convs[conv][idx]
        return (r["english"], r["roman"])

    def spk(n): return {"name": n, "role": "speaker"}
    def lis(n): return {"name": n, "role": "listener"}
    def sub(n, distance="far"): return {"name": n, "role": "subject", "distance": distance}

    SCENES = [
        ("Conversation 1", [
            ([spk("Raju"), spk("Shekhar")],
             [{"by": "Raju", "pairs": [P("1", 0)]}, {"by": "Shekhar", "pairs": [P("1", 1)]}]),
            ([spk("Raju")], [{"by": "Raju", "pairs": [P("1", 2)]}]),
            ([spk("Raju"), lis("Shekhar"), sub("Mohan", "near")], [{"by": "Raju", "pairs": [P("1", 3)]}]),
            ([spk("Raju"), sub("Shekhar")], [{"by": "Raju", "pairs": [P("1", 4)]}]),
            ([spk("Shekhar")], [{"by": "Shekhar", "pairs": [P("1", 5)]}]),
            ([spk("Raju"), lis("Shekhar"), sub("Sheela")], [{"by": "Raju", "pairs": [P("1", 6)]}]),
            ([spk("Shekhar"), lis("Raju"), sub("Sheela")], [{"by": "Shekhar", "pairs": [P("1", 7)]}]),
            ([spk("Shekhar"), lis("Raju"), sub("Shankar", "near")], [{"by": "Shekhar", "pairs": [P("1", 8)]}]),
        ]),
        ("Conversation 2", [
            ([spk("Raju")], [{"by": "Raju", "pairs": [P("2", 0), P("2", 1)]}]),
            ([spk("Raju"), lis("Shekhar"), sub("Mohan", "near")], [{"by": "Raju", "pairs": [P("2", 2), P("2", 3)]}]),
            ([spk("Raju"), sub("Shekhar")], [{"by": "Raju", "pairs": [P("2", 4)]}]),
            ([spk("Shekhar")], [{"by": "Shekhar", "pairs": [P("2", 5)]}]),
            ([spk("Raju"), sub("Shekhar")], [{"by": "Raju", "pairs": [P("2", 6)]}]),
            ([spk("Shekhar")], [{"by": "Shekhar", "pairs": [P("2", 7)]}]),
            ([spk("Raju"), lis("Shekhar"), sub("Lalita")], [{"by": "Raju", "pairs": [P("2", 8)]}]),
            ([spk("Shekhar"), lis("Raju"), sub("Lalita")], [{"by": "Shekhar", "pairs": [P("2", 9), P("2", 10)]}]),
            ([spk("Raju"), lis("Shekhar"), sub("Lalita")], [{"by": "Raju", "pairs": [P("2", 11)]}]),
            ([spk("Shekhar"), lis("Raju"), sub("Lalita")], [{"by": "Shekhar", "pairs": [P("2", 12), P("2", 13)]}]),
        ]),
        ("Conversation 3", [
            ([spk("Raju"), sub("Kiran")], [{"by": "Raju", "pairs": [P("3", 0)]}]),
            ([spk("Kiran")], [{"by": "Kiran", "pairs": [P("3", 1)]}]),
            ([spk("Raju"), lis("Kiran"), sub("Father")], [{"by": "Raju", "pairs": [P("3", 2)]}]),
            ([spk("Kiran"), lis("Raju"), sub("Father")], [{"by": "Kiran", "pairs": [P("3", 3)]}]),
        ]),
    ]

    body = []
    y = 0
    body.append(f'<text x="{W/2}" y="{y+46}" text-anchor="middle" font-size="34" '
                f'font-weight="800" fill="#c2410c">Lesson 1 — Meeting People</text>')
    body.append(f'<text x="{W/2}" y="{y+74}" text-anchor="middle" font-size="16" '
                f'fill="#7a6a58">Read the English, then say the Kannada underneath — watch who is pointing to whom!</text>')
    y += 98

    cast_h = 168
    body.append(f'<rect x="{PAD}" y="{y}" rx="18" width="{W-2*PAD}" height="{cast_h}" '
                f'fill="#fffaf2" stroke="#f3d9bf" stroke-width="2"/>')
    body.append(f'<text x="{W/2}" y="{y+26}" text-anchor="middle" font-size="15" '
                f'font-weight="700" fill="#9a3412">MEET THE CHARACTERS</text>')
    slot = (W - 2 * PAD) / len(CAST)
    for i, name in enumerate(CAST):
        cx = PAD + slot * i + slot / 2
        svg, _ = draw_person(cx, y + 70, PEOPLE[name], "neutral", 1)
        body.append(svg)
        body.append(name_tag(cx, y + 140, name, PEOPLE[name]["accent"]))
    y += cast_h + 22

    for title, panels in SCENES:
        body.append(f'<rect x="{PAD}" y="{y}" rx="12" width="{W-2*PAD}" height="36" fill="#7c3aed"/>')
        body.append(f'<text x="{W/2}" y="{y+24}" text-anchor="middle" font-size="17" '
                    f'font-weight="800" fill="#ffffff">{esc(title)}</text>')
        y += 36 + 16
        for chars, bubbles in panels:
            svg, h = render_panel(PAD, W - 2 * PAD, y, chars, bubbles)
            body.append(svg)
            y += h + 16
        y += 8

    y += PAD
    height = int(y)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
        f'viewBox="0 0 {W} {height}" font-family="Verdana,Arial,sans-serif">'
        f'<rect width="{W}" height="{height}" fill="#fff7ed"/>'
        f'<rect x="6" y="6" width="{W-12}" height="{height-12}" rx="22" fill="none" '
        f'stroke="#fcd9b6" stroke-width="3"/>'
        + "".join(body) + "</svg>"
    )


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    svg = build()
    OUT.with_suffix(".svg").write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT.with_suffix('.svg')}")
    try:
        import cairosvg
        cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                         write_to=str(OUT.with_suffix(".png")), output_width=W * 2)
        print(f"Wrote {OUT.with_suffix('.png')}")
    except Exception as e:
        print(f"(PNG export skipped: {e})")


if __name__ == "__main__":
    main()
