import { NextResponse } from "next/server";
import { getCurrentSession } from "@/lib/auth-session";
import { ensureAppUser, getUserProgress } from "@/lib/progress";

export const runtime = "nodejs";

export async function GET() {
  const session = await getCurrentSession();
  if (!session) {
    return NextResponse.json(
      { error: "Sign in to view progress." },
      { status: 401 }
    );
  }

  const user = await ensureAppUser(session);
  if (!user) {
    return NextResponse.json(
      { error: "Could not load progress user." },
      { status: 500 }
    );
  }

  const progress = await getUserProgress(user.id);
  return NextResponse.json({ user, progress });
}
