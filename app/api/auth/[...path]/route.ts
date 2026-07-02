import { NextResponse } from "next/server";
import { auth } from "@/auth";

export const runtime = "nodejs";

const handler = auth.handler();

function missingConfigResponse() {
  return NextResponse.json(
    {
      error:
        "Neon Auth is not configured yet. Set NEON_AUTH_BASE_URL and restart the dev server.",
      code: "NEON_AUTH_NOT_CONFIGURED",
    },
    { status: 503 },
  );
}

function isConfigured() {
  return Boolean(process.env.NEON_AUTH_BASE_URL);
}

export function GET(...args: Parameters<typeof handler.GET>) {
  if (!isConfigured()) return missingConfigResponse();
  return handler.GET(...args);
}

export function POST(...args: Parameters<typeof handler.POST>) {
  if (!isConfigured()) return missingConfigResponse();
  return handler.POST(...args);
}

export function PUT(...args: Parameters<typeof handler.PUT>) {
  if (!isConfigured()) return missingConfigResponse();
  return handler.PUT(...args);
}

export function DELETE(...args: Parameters<typeof handler.DELETE>) {
  if (!isConfigured()) return missingConfigResponse();
  return handler.DELETE(...args);
}

export function PATCH(...args: Parameters<typeof handler.PATCH>) {
  if (!isConfigured()) return missingConfigResponse();
  return handler.PATCH(...args);
}
