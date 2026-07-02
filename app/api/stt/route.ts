import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

const SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text";

function filenameForAudio(file: File): string {
  const type = audioContentType(file);
  if (type.includes("webm")) return "practice.webm";
  if (type.includes("mp4") || type.includes("m4a")) return "practice.m4a";
  if (type.includes("mpeg") || type.includes("mp3")) return "practice.mp3";
  if (type.includes("wav")) return "practice.wav";
  return file.name || "practice.webm";
}

function audioContentType(file: File): string {
  return (file.type || "audio/webm").toLowerCase().split(";")[0].trim();
}

function normalizeRoman(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\b(mr|mrs|miss|speaker|a|b|c)\b/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .split(" ")
    .map((word) => word.replace(/([aeiou])\1+/g, "$1"))
    .join(" ");
}

function levenshtein(a: string, b: string): number {
  if (a === b) return 0;
  if (!a) return b.length;
  if (!b) return a.length;
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  let cur = new Array<number>(b.length + 1);
  for (let i = 1; i <= a.length; i++) {
    cur[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      cur[j] = Math.min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost);
    }
    [prev, cur] = [cur, prev];
  }
  return prev[b.length];
}

function similarity(a: string, b: string): number {
  const maxLength = Math.max(a.length, b.length);
  if (!maxLength) return 0;
  return 1 - levenshtein(a, b) / maxLength;
}

function tokens(value: string): string[] {
  return value.split(/\s+/).filter(Boolean);
}

function tokenRecall(expected: string[], actual: string[]): number {
  if (!expected.length) return 0;
  const actualSet = new Set(actual);
  return expected.filter((token) => actualSet.has(token)).length / expected.length;
}

function phraseMatches(expected: string, actual: string, score: number): boolean {
  if (!expected || !actual) return false;
  if (expected === actual) return true;

  const expectedTokens = tokens(expected);
  const actualTokens = tokens(actual);
  const recall = tokenRecall(expectedTokens, actualTokens);
  const sameTokenCount = expectedTokens.length === actualTokens.length;

  // Short learner phrases often contain names, so "naanu rama" must not pass
  // for "naanu raju" just because the edit distance is small.
  if (expectedTokens.length <= 4) {
    return sameTokenCount && recall === 1 && score >= 0.92;
  }

  return recall >= 0.78 && score >= 0.86;
}

async function readJsonOrText(resp: Response): Promise<any> {
  const contentType = resp.headers.get("content-type") || "";
  const body = await resp.text();
  if (!body) return {};
  if (contentType.includes("application/json")) {
    try {
      return JSON.parse(body);
    } catch {
      return { raw: body };
    }
  }
  try {
    return JSON.parse(body);
  } catch {
    return { raw: body };
  }
}

export async function POST(req: NextRequest) {
  const key = process.env.SARVAM_API_KEY;
  if (!key) {
    return NextResponse.json(
      { error: "SARVAM_API_KEY is not configured on the server." },
      { status: 500 }
    );
  }

  let incoming: FormData;
  try {
    incoming = await req.formData();
  } catch {
    return NextResponse.json({ error: "Invalid multipart form." }, { status: 400 });
  }

  const file = incoming.get("file");
  const expected = String(incoming.get("expected") ?? "").trim();
  if (!(file instanceof File)) {
    return NextResponse.json({ error: "Missing audio file." }, { status: 400 });
  }
  if (!expected) {
    return NextResponse.json({ error: "Missing expected phrase." }, { status: 400 });
  }

  const uploadFile = new Blob([await file.arrayBuffer()], {
    type: audioContentType(file),
  });
  const body = new FormData();
  body.set("file", uploadFile, filenameForAudio(file));
  body.set("model", "saaras:v3");
  body.set("mode", "translit");
  body.set("language_code", "kn-IN");

  try {
    const resp = await fetch(SARVAM_STT_URL, {
      method: "POST",
      headers: {
        "api-subscription-key": key,
      },
      body,
    });

    const data = await readJsonOrText(resp);

    if (!resp.ok) {
      console.error("Sarvam STT failed", {
        status: resp.status,
        fileType: file.type,
        fileName: file.name,
        fileSize: file.size,
        detail: data,
      });
      return NextResponse.json(
        {
          error: "Speech recognition failed.",
          detail: data,
          fileType: file.type,
          fileName: file.name,
          fileSize: file.size,
        },
        { status: 502 }
      );
    }

    const transcript = String(data?.transcript ?? "").trim();
    const expectedNormalized = normalizeRoman(expected);
    const transcriptNormalized = normalizeRoman(transcript);
    const score = similarity(expectedNormalized, transcriptNormalized);
    const matched = phraseMatches(expectedNormalized, transcriptNormalized, score);

    return NextResponse.json({
      transcript,
      transcriptNormalized,
      expectedNormalized,
      score,
      matched,
      languageCode: data?.language_code ?? null,
    });
  } catch (err) {
    return NextResponse.json(
      { error: "Unexpected speech recognition error.", detail: String(err) },
      { status: 500 }
    );
  }
}
