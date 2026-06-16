"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { api, ApiError } from "@/lib/api";

function ResetPasswordForm() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords don't match.");
      return;
    }
    setBusy(true);
    try {
      await api.confirmPasswordReset(token, password);
      setDone(true);
      setTimeout(() => router.push("/login"), 1500);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not reset your password.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <p className="text-sm text-red-400">
        This link is missing its token. Request a new reset email from{" "}
        <Link href="/forgot-password" className="text-orange-400 hover:underline">
          here
        </Link>
        .
      </p>
    );
  }

  if (done) {
    return (
      <p className="rounded-md border border-orange-400/30 bg-orange-400/10 p-3 text-sm text-orange-200">
        Password reset. Redirecting you to log in…
      </p>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="New password"
        className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 outline-none focus:border-orange-400"
      />
      <input
        type="password"
        value={confirm}
        onChange={(e) => setConfirm(e.target.value)}
        placeholder="Confirm new password"
        className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 outline-none focus:border-orange-400"
      />
      {error && <p className="text-sm text-red-400">{error}</p>}
      <button
        disabled={busy}
        className="w-full rounded-md bg-orange-500 px-3 py-2 font-medium text-black hover:bg-orange-400 disabled:opacity-50"
      >
        {busy ? "Saving…" : "Set new password"}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-6 text-2xl font-bold">Choose a new password</h1>
      <Suspense fallback={<p className="text-white/50">Loading…</p>}>
        <ResetPasswordForm />
      </Suspense>
    </div>
  );
}
