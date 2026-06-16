"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import ListCard from "@/components/ListCard";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ListSummary } from "@/lib/types";

export default function ListsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [lists, setLists] = useState<ListSummary[] | null>(null);

  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isRanked, setIsRanked] = useState(false);
  const [isPublic, setIsPublic] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (user) api.myLists().then(setLists).catch(() => setLists([]));
  }, [user]);

  if (loading || !user) return <p className="text-white/50">Loading…</p>;

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const created = await api.createList({
        title: title.trim(),
        description: description.trim() || null,
        is_ranked: isRanked,
        is_public: isPublic,
      });
      router.push(`/lists/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create list.");
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Your lists</h1>
          <p className="text-sm text-white/50">Curate and rank films your way.</p>
        </div>
        <button
          onClick={() => setCreating((c) => !c)}
          className="rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-black hover:bg-orange-400"
        >
          {creating ? "Cancel" : "New list"}
        </button>
      </div>

      {creating && (
        <form
          onSubmit={onCreate}
          className="mb-8 space-y-4 rounded-lg border border-white/10 bg-white/[0.03] p-4"
        >
          <div>
            <label className="mb-1 block text-sm text-white/70">Title</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={200}
              autoFocus
              placeholder="e.g. Best heist films"
              className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 text-sm outline-none focus:border-orange-400"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-white/70">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={2000}
              rows={2}
              placeholder="Optional"
              className="w-full resize-y rounded-md border border-white/15 bg-white/5 px-3 py-2 text-sm outline-none focus:border-orange-400"
            />
          </div>
          <div className="flex gap-6 text-sm">
            <label className="flex items-center gap-2 text-white/70">
              <input
                type="checkbox"
                checked={isRanked}
                onChange={(e) => setIsRanked(e.target.checked)}
                className="accent-orange-500"
              />
              Ranked
            </label>
            <label className="flex items-center gap-2 text-white/70">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                className="accent-orange-500"
              />
              Public
            </label>
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={busy || !title.trim()}
            className="rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-black hover:bg-orange-400 disabled:opacity-60"
          >
            {busy ? "Creating…" : "Create list"}
          </button>
        </form>
      )}

      {!lists && <p className="text-white/50">Loading…</p>}
      {lists && lists.length === 0 && !creating && (
        <p className="text-white/50">
          No lists yet. Hit <span className="text-orange-400">New list</span> to start one.
        </p>
      )}
      {lists && lists.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {lists.map((l) => (
            <ListCard key={l.id} list={l} />
          ))}
        </div>
      )}
    </div>
  );
}
