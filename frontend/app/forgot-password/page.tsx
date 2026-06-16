"use client";

import Link from "next/link";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await api.requestPasswordReset(email.trim());
      setMessage(res.detail);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-2 text-2xl font-bold">Reset your password</h1>
      <p className="mb-6 text-sm text-white/60">
        Enter your email and we&apos;ll send you a link to choose a new password.
      </p>

      {message ? (
        <p className="rounded-md border border-orange-400/30 bg-orange-400/10 p-3 text-sm text-orange-200">
          {message}
        </p>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4">
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 outline-none focus:border-orange-400"
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            disabled={busy}
            className="w-full rounded-md bg-orange-500 px-3 py-2 font-medium text-black hover:bg-orange-400 disabled:opacity-50"
          >
            {busy ? "Sending…" : "Send reset link"}
          </button>
        </form>
      )}

      <p className="mt-4 text-sm text-white/60">
        <Link href="/login" className="text-orange-400 hover:underline">
          Back to log in
        </Link>
      </p>
    </div>
  );
}
