import { createNeonAuth } from "@neondatabase/auth/next/server";

const developmentCookieSecret =
  "development-only-neon-auth-cookie-secret-change-me";

export const auth = createNeonAuth({
  baseUrl: process.env.NEON_AUTH_BASE_URL ?? "",
  cookies: {
    secret:
      process.env.NEON_AUTH_COOKIE_SECRET ??
      process.env.AUTH_SECRET ??
      developmentCookieSecret,
    sessionDataTtl: 300,
  },
});
