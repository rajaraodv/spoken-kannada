"use client";

import { Suspense, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

function cleanCallbackUrl(value: string | null) {
  if (!value || !value.startsWith("/")) return "/";
  if (value.startsWith("//")) return "/";
  return value;
}

function errorMessage(data: unknown, fallback: string) {
  if (!data || typeof data !== "object") return fallback;
  const body = data as {
    error?: string | { message?: string };
    message?: string;
  };
  if (typeof body.error === "string") return body.error;
  if (body.error?.message) return body.error.message;
  if (body.message) return body.message;
  return fallback;
}

function SignInForm() {
  const searchParams = useSearchParams();
  const callbackUrl = useMemo(
    () => cleanCallbackUrl(searchParams.get("callbackUrl")),
    [searchParams],
  );
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<"email" | "code">("email");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function sendCode(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setStatus("");

    try {
      const response = await fetch("/api/auth/email-otp/send-verification-otp", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          type: "sign-in",
        }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok || data?.error) {
        throw new Error(errorMessage(data, "Could not send the code."));
      }
      setStep("code");
      setStatus("Check your email. We sent you a short sign-in code.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send the code.");
    } finally {
      setBusy(false);
    }
  }

  async function verifyCode(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setStatus("");

    try {
      const response = await fetch("/api/auth/sign-in/email-otp", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          otp: otp.trim(),
        }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok || data?.error) {
        throw new Error(errorMessage(data, "That code did not work."));
      }
      window.location.assign(callbackUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : "That code did not work.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
      <div className="mb-7">
        <p className="text-sm font-bold uppercase tracking-[0.18em] text-slate-500">
          Passwordless Sign In
        </p>
        <h1 className="mt-3 text-4xl font-black tracking-normal text-slate-950">
          Get a code by email
        </h1>
        <p className="mt-3 text-lg font-medium leading-8 text-slate-600">
          Enter your email address. We will send a short one-time code. Type the
          code here, and you are in. No password to remember.
        </p>
      </div>

      {step === "email" ? (
        <form className="grid gap-4" onSubmit={sendCode}>
          <label className="grid gap-2">
            <span className="text-sm font-black uppercase tracking-[0.12em] text-slate-500">
              Email address
            </span>
            <input
              className="h-14 rounded-xl border border-slate-300 px-4 text-lg font-bold text-slate-950 outline-none transition focus:border-slate-950"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
            />
          </label>
          <button
            className="h-14 rounded-xl bg-slate-950 px-5 text-lg font-black text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={busy}
            type="submit"
          >
            {busy ? "Sending code..." : "Send my code"}
          </button>
        </form>
      ) : (
        <form className="grid gap-4" onSubmit={verifyCode}>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-bold text-slate-500">Code sent to</p>
            <p className="mt-1 text-lg font-black text-slate-950">{email}</p>
          </div>
          <label className="grid gap-2">
            <span className="text-sm font-black uppercase tracking-[0.12em] text-slate-500">
              One-time code
            </span>
            <input
              className="h-14 rounded-xl border border-slate-300 px-4 text-center text-2xl font-black tracking-[0.18em] text-slate-950 outline-none transition focus:border-slate-950"
              inputMode="numeric"
              autoComplete="one-time-code"
              required
              value={otp}
              onChange={(event) => setOtp(event.target.value)}
              placeholder="123456"
            />
          </label>
          <button
            className="h-14 rounded-xl bg-slate-950 px-5 text-lg font-black text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={busy}
            type="submit"
          >
            {busy ? "Checking code..." : "Sign in"}
          </button>
          <button
            className="h-12 rounded-xl border border-slate-300 bg-white px-5 text-base font-black text-slate-900 transition hover:border-slate-950"
            disabled={busy}
            type="button"
            onClick={() => {
              setStep("email");
              setOtp("");
              setStatus("");
              setError("");
            }}
          >
            Use a different email
          </button>
        </form>
      )}

      {status ? (
        <p className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4 font-bold text-emerald-800">
          {status}
        </p>
      ) : null}
      {error ? (
        <p className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 font-bold text-red-700">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export default function SignInPage() {
  return (
    <main className="min-h-screen bg-[#f8fafc] px-5 py-10 text-slate-950">
      <section className="mx-auto grid w-full max-w-5xl gap-8 lg:grid-cols-[1fr_0.8fr] lg:items-center">
        <Suspense>
          <SignInForm />
        </Suspense>
        <aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <h2 className="text-2xl font-black">How it works</h2>
          <div className="mt-5 grid gap-4 text-base font-semibold leading-7 text-slate-600">
            <p>1. Type your email address.</p>
            <p>2. Open your inbox and find the one-time code.</p>
            <p>3. Enter the code here to start saving progress.</p>
          </div>
          <div className="mt-7 rounded-2xl bg-slate-50 p-5">
            <p className="font-bold leading-7 text-slate-600">
              This is easier for families because there is no password to make,
              store, or remember.
            </p>
          </div>
          <Link
            className="mt-6 inline-flex rounded-xl border border-slate-300 bg-white px-5 py-3 font-black text-slate-900 transition hover:border-slate-950"
            href="/"
          >
            Back to chapters
          </Link>
        </aside>
      </section>
    </main>
  );
}
