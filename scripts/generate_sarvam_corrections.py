#!/usr/bin/env python3
"""Generate Sarvam translation corrections for selected chapters.

This keeps the original PDF romanization intact and adds a correction layer:
English -> Kannada script, plus Sarvam roman output.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


DATA_PATH = Path("data/page_by_page_conversations.json")
OUT_PATH = Path("data/sarvam_corrections_all_chapters.json")
ENV_PATH = Path(".env.local")
CHAPTERS: set[int] | None = None
SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"
TRANSLATION_MODE = "formal"
SOURCE_ID = f"sarvam_translate_mayura_v1_{TRANSLATION_MODE}"
MAX_WORKERS = int(os.environ.get("SARVAM_TRANSLATE_WORKERS", "1"))
VERBOSE = os.environ.get("VERBOSE_CORRECTIONS") == "1"


def load_env() -> None:
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def assign_chapters(conversations: list[dict]) -> list[tuple[int, dict]]:
    assigned: list[tuple[int, dict]] = []
    current: int | None = None
    for conv in conversations:
        if conv.get("lesson") is not None:
            current = int(conv["lesson"])
        if current is not None:
            assigned.append((current, conv))
    return assigned


def clean_english(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\\", "")).strip(" ;:")


def correction_key(chapter: int, conv: str, row: int) -> str:
    return f"chapter-{chapter:02d}:conversation-{conv}:row-{row:02d}"


def write_cache(corrections: dict) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(corrections, ensure_ascii=False, indent=2), encoding="utf-8")


def translate(text: str, output_script: str, key: str) -> str:
    payload = {
        "input": text,
        "source_language_code": "en-IN",
        "target_language_code": "kn-IN",
        "speaker_gender": "Male",
        "mode": TRANSLATION_MODE,
        "model": "mayura:v1",
        "output_script": output_script,
        "enable_preprocessing": True,
    }
    req = urllib.request.Request(
        SARVAM_TRANSLATE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "api-subscription-key": key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return str(body["translated_text"]).strip()
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", errors="replace")
            if err.code in {429, 500, 502, 503, 504} and attempt < 7:
                retry_after = err.headers.get("retry-after")
                if retry_after and retry_after.isdigit():
                    wait = int(retry_after)
                elif err.code == 429:
                    wait = 30 + attempt * 15
                else:
                    wait = 4 + attempt * 4
                time.sleep(wait)
                continue
            raise RuntimeError(f"Sarvam translate failed for {text!r}: {detail}") from err
        except (TimeoutError, urllib.error.URLError):
            if attempt == 7:
                raise
            time.sleep(2 + attempt * 2)
    raise RuntimeError(f"Sarvam translate failed for {text!r}")


def correction_for_task(task: dict, api_key: str) -> tuple[str, dict]:
    english = task["english"]
    kannada = translate(english, "fully-native", api_key)
    roman = translate(english, "roman", api_key)
    return task["key_id"], {
        "chapter": task["chapter"],
        "conversation": task["conversation"],
        "row": task["row"],
        "english": english,
        "original_roman": task["original_roman"],
        "sarvam_kannada": kannada,
        "sarvam_roman": roman,
        "source": SOURCE_ID,
    }


def main() -> None:
    load_env()
    key = os.environ.get("SARVAM_API_KEY")
    if not key:
        raise SystemExit("SARVAM_API_KEY is not configured.")

    conversations = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    existing = json.loads(OUT_PATH.read_text(encoding="utf-8")) if OUT_PATH.exists() else {}
    corrections = dict(existing)

    pending: list[dict] = []
    for chapter, conv in assign_chapters(conversations):
        if CHAPTERS is not None and chapter not in CHAPTERS:
            continue
        conv_number = str(conv["number"])
        for row_index, row in enumerate(conv["rows"], 1):
            english = clean_english(str(row.get("english") or ""))
            if not english:
                continue
            key_id = correction_key(chapter, conv_number, row_index)
            cached = corrections.get(key_id)
            if cached and cached.get("english") == english and cached.get("source") == SOURCE_ID:
                continue
            pending.append({
                "chapter": chapter,
                "conversation": conv_number,
                "row": row_index,
                "key_id": key_id,
                "english": english,
                "original_roman": row.get("roman", ""),
            })

    total = len(pending)
    if not total:
        write_cache(corrections)
        print(f"Wrote {OUT_PATH} with {len(corrections)} corrections (0 new)")
        return

    print(
        f"Translating {total} remaining rows with {MAX_WORKERS} workers; "
        f"{len(corrections)} cached rows already present.",
        flush=True,
    )

    added = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(correction_for_task, task, key) for task in pending]
        for future in as_completed(futures):
            try:
                key_id, correction = future.result()
            except Exception as err:
                print(f"Skipped one row after retries: {err}", flush=True)
                continue
            corrections[key_id] = correction
            added += 1
            write_cache(corrections)
            if VERBOSE:
                print(
                    f"{key_id}: {correction['english']} -> "
                    f"{correction['sarvam_roman']} / {correction['sarvam_kannada']}",
                    flush=True,
                )
            elif added == 1 or added % 25 == 0 or added == total:
                print(f"Translated {added}/{total}; cache now has {len(corrections)} rows.", flush=True)

    write_cache(corrections)
    print(f"Wrote {OUT_PATH} with {len(corrections)} corrections ({added} new)")


if __name__ == "__main__":
    main()
