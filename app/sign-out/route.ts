import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/auth";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const callbackUrl = request.nextUrl.searchParams.get("callbackUrl") || "/";
  await auth.signOut();
  return NextResponse.redirect(new URL(callbackUrl, request.url));
}
