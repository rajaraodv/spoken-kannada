import { NextResponse } from "next/server";
import { getCurrentSession } from "@/lib/auth-session";
import { ensureAppUser, getUserProgress } from "@/lib/progress";

export const runtime = "nodejs";

export async function GET() {
  const session = await getCurrentSession();
  if (!session) {
    return NextResponse.json({ authenticated: false });
  }

  const user = await ensureAppUser(session);
  if (!user) {
    return NextResponse.json({ authenticated: false });
  }

  const progress = await getUserProgress(user.id);
  return NextResponse.json({
    authenticated: true,
    user,
    progress,
  });
}
