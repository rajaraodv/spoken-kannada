# Spoken Kannada Chapters

A simple Next.js wrapper around generated spoken Kannada chapter pages.

The active learning experience is the generated HTML under `public/chapters`.
Each chapter page contains visual conversation cards, English audio, Kannada
audio, and Kannada speech practice through Sarvam.

## Run

```bash
npm install
npm run dev
```

Open:

- `http://localhost:3000` for the chapter launcher
- `http://localhost:3000/chapters/chapter-03.html` for a direct chapter page

## Build

```bash
npm run build:chapters
npm run build
```

## Image Generation

Use the personal Codex skill `spoken-kannada-conversation-images` before
generating or replacing chapter images. The skill requires each prompt to carry
the full conversation context, current sentence, speaker/listener names, English
and Kannada speech-bubble text, scene setting, and previous-image continuity.

## Project Map

| Path | Purpose |
| --- | --- |
| `app/page.tsx` | Minimal chapter launcher |
| `app/api/tts/route.ts` | Sarvam text-to-speech proxy |
| `app/api/stt/route.ts` | Sarvam speech-to-text practice proxy |
| `public/chapters/` | Generated chapter HTML pages |
| `public/images/chapter-visuals/` | Generated SVG practice visuals |
| `data/page_by_page_conversations.json` | Extracted chapter conversation data |
| `data/sarvam_corrections_all_chapters.json` | Sarvam Kannada script and roman corrections |
| `scripts/build_page_by_page_html.py` | Generates chapter HTML from data |
| `scripts/generate_sarvam_corrections.py` | Generates Sarvam corrections |

Set `SARVAM_API_KEY` in `.env.local` for audio and speech practice.
