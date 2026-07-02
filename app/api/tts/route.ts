import { NextRequest, NextResponse } from "next/server";

// Server-side TTS proxy. The Sarvam key never reaches the browser.
export const runtime = "nodejs";

const SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech";

export async function POST(req: NextRequest) {
  const key = process.env.SARVAM_API_KEY;
  if (!key) {
    return NextResponse.json(
      { error: "SARVAM_API_KEY is not configured on the server." },
      { status: 500 }
    );
  }

  let text: string;
  let languageCode: string;
  let speaker: string | undefined;
  try {
    const body = await req.json();
    text = String(body.text ?? "").trim();
    languageCode = String(body.languageCode ?? body.lang ?? "kn-IN").trim();
    speaker = body.speaker ? String(body.speaker) : undefined;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  if (!text) {
    return NextResponse.json({ error: "Missing 'text'." }, { status: 400 });
  }

  if (!["kn-IN", "en-IN"].includes(languageCode)) {
    return NextResponse.json(
      { error: "Unsupported languageCode. Use 'kn-IN' or 'en-IN'." },
      { status: 400 }
    );
  }

  try {
    const resp = await fetch(SARVAM_TTS_URL, {
      method: "POST",
      headers: {
        "api-subscription-key": key,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        target_language_code: languageCode,
        speaker: speaker || (languageCode === "en-IN" ? "shubh" : "priya"),
        model: "bulbul:v3",
        pace: 0.9, // a touch slower — easier for learners to follow
        enable_preprocessing: true,
        speech_sample_rate: 22050,
      }),
    });

    if (!resp.ok) {
      const detail = await resp.text();
      return NextResponse.json(
        { error: "TTS request failed.", detail },
        { status: 502 }
      );
    }

    const data = await resp.json();
    const audioBase64: string | undefined =
      data?.audios?.[0] ?? data?.audio ?? data?.audio_base64;
    if (!audioBase64) {
      return NextResponse.json(
        { error: "No audio returned from TTS." },
        { status: 502 }
      );
    }

    const buffer = Buffer.from(audioBase64, "base64");
    return new NextResponse(buffer, {
      status: 200,
      headers: {
        "Content-Type": "audio/wav",
        "Cache-Control": "public, max-age=86400",
      },
    });
  } catch (err) {
    return NextResponse.json(
      { error: "Unexpected TTS error.", detail: String(err) },
      { status: 500 }
    );
  }
}
