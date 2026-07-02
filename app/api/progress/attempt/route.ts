import { NextRequest, NextResponse } from "next/server";
import { getCurrentSession } from "@/lib/auth-session";
import { ensureAppUser, recordPracticeAttempt } from "@/lib/progress";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const session = await getCurrentSession();
  if (!session) {
    return NextResponse.json(
      { error: "Sign in to save progress." },
      { status: 401 }
    );
  }

  const user = await ensureAppUser(session);
  if (!user) {
    return NextResponse.json(
      { error: "Could not create progress user." },
      { status: 500 }
    );
  }

  let body: {
    chapter?: unknown;
    conversationId?: unknown;
    sceneIndex?: unknown;
    expected?: unknown;
    transcript?: unknown;
    score?: unknown;
    matched?: unknown;
  };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const chapter = Number(body.chapter);
  const sceneIndex = Number(body.sceneIndex);
  const conversationId = String(body.conversationId ?? "").trim();
  const expected = String(body.expected ?? "").trim();
  const transcript = String(body.transcript ?? "").trim();
  const score = typeof body.score === "number" ? body.score : null;
  const matched = body.matched === true;

  if (!Number.isInteger(chapter) || chapter < 1) {
    return NextResponse.json({ error: "Invalid chapter." }, { status: 400 });
  }
  if (!Number.isInteger(sceneIndex) || sceneIndex < 1) {
    return NextResponse.json({ error: "Invalid sceneIndex." }, { status: 400 });
  }
  if (!conversationId) {
    return NextResponse.json({ error: "Missing conversationId." }, { status: 400 });
  }

  const progress = await recordPracticeAttempt({
    userId: user.id,
    chapter,
    conversationId,
    sceneIndex,
    expected,
    transcript,
    score,
    matched,
  });

  return NextResponse.json({ saved: true, user, progress });
}
