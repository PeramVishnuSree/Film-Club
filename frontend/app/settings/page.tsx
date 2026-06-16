"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function SettingsPage() {
  const { user, loading, setUser } = useAuth();
  const router = useRouter();

  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [region, setRegion] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [verifyMsg, setVerifyMsg] = useState<string | null>(null);
  const [verifyBusy, setVerifyBusy] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  // Seed the editable form fields from the loaded user. This intentionally
  // syncs server state into local form state, which the lint rule flags.
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name ?? "");
      setBio(user.bio ?? "");
      setAvatarUrl(user.avatar_url ?? "");
      setRegion(user.region ?? "US");
    }
  }, [user]);
  /* eslint-enable react-hooks/set-state-in-effect */

  if (loading || !user) return <p className="text-white/50">Loading…</p>;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const updated = await api.updateProfile({
        display_name: displayName.trim() || null,
        bio: bio.trim() || null,
        avatar_url: avatarUrl.trim() || null,
        region: region.trim().toUpperCase() || undefined,
      });
      setUser(updated);
      setSaved(true);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not save changes.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function onResendVerification() {
    setVerifyBusy(true);
    setVerifyMsg(null);
    try {
      const res = await api.requestEmailVerification();
      setVerifyMsg(res.detail);
    } catch (err) {
      setVerifyMsg(
        err instanceof ApiError ? err.message : "Could not send the email.",
      );
    } finally {
      setVerifyBusy(false);
    }
  }

  return (
    <div className="max-w-lg">
      <h1 className="mb-1 text-2xl font-bold">Edit profile</h1>
      <p className="mb-6 text-sm text-white/50">
        How you appear at{" "}
        <Link href={`/u/${user.username}`} className="text-orange-400 hover:underline">
          @{user.username}
        </Link>
        .
      </p>

      {!user.email_verified && (
        <div className="mb-6 rounded-md border border-yellow-400/30 bg-yellow-400/10 p-3 text-sm text-yellow-200">
          <p className="mb-2">
            Your email address ({user.email}) isn&apos;t verified yet.
          </p>
          {verifyMsg ? (
            <p className="text-yellow-100">{verifyMsg}</p>
          ) : (
            <button
              onClick={onResendVerification}
              disabled={verifyBusy}
              className="rounded-md bg-yellow-400/20 px-3 py-1 font-medium text-yellow-100 hover:bg-yellow-400/30 disabled:opacity-50"
            >
              {verifyBusy ? "Sending…" : "Resend verification email"}
            </button>
          )}
        </div>
      )}

      <form onSubmit={onSubmit} className="space-y-5">
        <div>
          <label className="mb-1 block text-sm text-white/70">Display name</label>
          <input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            maxLength={80}
            placeholder={user.username}
            className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 text-sm outline-none focus:border-orange-400"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-white/70">Bio</label>
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            maxLength={500}
            rows={4}
            placeholder="Tell people what you watch…"
            className="w-full resize-y rounded-md border border-white/15 bg-white/5 px-3 py-2 text-sm outline-none focus:border-orange-400"
          />
          <p className="mt-1 text-right text-xs text-white/30">{bio.length}/500</p>
        </div>

        <div>
          <label className="mb-1 block text-sm text-white/70">Avatar URL</label>
          <input
            value={avatarUrl}
            onChange={(e) => setAvatarUrl(e.target.value)}
            maxLength={500}
            placeholder="https://…"
            className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 text-sm outline-none focus:border-orange-400"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-white/70">
            Region <span className="text-white/30">(2-letter, drives streaming results)</span>
          </label>
          <input
            value={region}
            onChange={(e) => setRegion(e.target.value.toUpperCase())}
            maxLength={2}
            placeholder="US"
            className="w-24 rounded-md border border-white/15 bg-white/5 px-3 py-2 text-sm uppercase outline-none focus:border-orange-400"
          />
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}
        {saved && <p className="text-sm text-orange-400">Saved.</p>}

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-black hover:bg-orange-400 disabled:opacity-60"
          >
            {saving ? "Saving…" : "Save changes"}
          </button>
          <Link
            href={`/u/${user.username}`}
            className="text-sm text-white/60 hover:text-white"
          >
            View profile
          </Link>
        </div>
      </form>

      <div className="mt-10 border-t border-white/10 pt-6">
        <h2 className="text-lg font-semibold">Import</h2>
        <p className="mt-1 text-sm text-white/50">
          Bring your history over from Letterboxd.{" "}
          <Link href="/import" className="text-orange-400 hover:underline">
            Import a CSV
          </Link>
        </p>
      </div>
    </div>
  );
}
