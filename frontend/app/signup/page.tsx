"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function SignupPage() {
  const { signup } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    display_name: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function update(key: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await signup({
        username: form.username,
        email: form.email,
        password: form.password,
        display_name: form.display_name || undefined,
      });
      router.push("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Sign up failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-6 text-2xl font-bold">Create your account</h1>
      <form onSubmit={onSubmit} className="space-y-4">
        <input
          value={form.username}
          onChange={update("username")}
          placeholder="Username"
          className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 outline-none focus:border-emerald-400"
        />
        <input
          value={form.display_name}
          onChange={update("display_name")}
          placeholder="Display name (optional)"
          className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 outline-none focus:border-emerald-400"
        />
        <input
          type="email"
          value={form.email}
          onChange={update("email")}
          placeholder="Email"
          className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 outline-none focus:border-emerald-400"
        />
        <input
          type="password"
          value={form.password}
          onChange={update("password")}
          placeholder="Password (min 8 chars)"
          className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 outline-none focus:border-emerald-400"
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          disabled={busy}
          className="w-full rounded-md bg-emerald-500 px-3 py-2 font-medium text-black hover:bg-emerald-400 disabled:opacity-50"
        >
          {busy ? "Creating…" : "Sign up"}
        </button>
      </form>
      <p className="mt-4 text-sm text-white/60">
        Already have an account?{" "}
        <Link href="/login" className="text-emerald-400 hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
