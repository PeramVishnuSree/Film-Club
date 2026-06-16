"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { ListSummary } from "@/lib/types";

export default function AddToListButton({ tmdbId }: { tmdbId: number }) {
  const [open, setOpen] = useState(false);
  const [lists, setLists] = useState<ListSummary[] | null>(null);
  const [added, setAdded] = useState<Set<number>>(new Set());
  const [msg, setMsg] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [creating, setCreating] = useState(false);

  async function toggleOpen() {
    const next = !open;
    setOpen(next);
    setMsg(null);
    if (next && lists === null) {
      try {
        setLists(await api.myLists());
      } catch {
        setLists([]);
      }
    }
  }

  async function addTo(list: ListSummary) {
    setMsg(null);
    try {
      await api.addListItem(list.id, tmdbId);
      setAdded((s) => new Set(s).add(list.id));
      setMsg(`Added to “${list.title}”.`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setAdded((s) => new Set(s).add(list.id));
        setMsg(`Already in “${list.title}”.`);
      } else {
        setMsg("Could not add to list.");
      }
    }
  }

  async function createAndAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!newTitle.trim()) return;
    setCreating(true);
    setMsg(null);
    try {
      const created = await api.createList({ title: newTitle.trim() });
      await api.addListItem(created.id, tmdbId);
      const summary: ListSummary = {
        id: created.id,
        title: created.title,
        description: created.description,
        is_ranked: created.is_ranked,
        is_public: created.is_public,
        is_system: created.is_system,
        item_count: 1,
        owner: created.owner,
        created_at: created.created_at,
        preview_posters: created.preview_posters,
      };
      setLists((ls) => [summary, ...(ls ?? [])]);
      setAdded((s) => new Set(s).add(created.id));
      setNewTitle("");
      setMsg(`Created and added to “${created.title}”.`);
    } catch {
      setMsg("Could not create list.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-4">
      <button
        onClick={toggleOpen}
        className="flex w-full items-center justify-between text-sm font-medium"
      >
        <span className="text-xs uppercase tracking-wide text-white/50">
          Add to list
        </span>
        <span className="text-white/40">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="mt-3 space-y-3">
          {lists === null && <p className="text-sm text-white/50">Loading…</p>}
          {lists && lists.length > 0 && (
            <ul className="max-h-56 space-y-1 overflow-y-auto">
              {lists.map((l) => (
                <li key={l.id}>
                  <button
                    onClick={() => addTo(l)}
                    disabled={added.has(l.id)}
                    className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-sm hover:bg-white/10 disabled:opacity-50"
                  >
                    <span className="truncate">{l.title}</span>
                    <span className="ml-2 shrink-0 text-xs text-white/40">
                      {added.has(l.id) ? "✓" : "+"}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          <form onSubmit={createAndAdd} className="flex gap-2">
            <input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="New list…"
              maxLength={200}
              className="flex-1 rounded-md border border-white/15 bg-white/5 px-2 py-1.5 text-sm outline-none focus:border-orange-400"
            />
            <button
              type="submit"
              disabled={creating || !newTitle.trim()}
              className="rounded-md bg-orange-500 px-3 py-1.5 text-sm font-medium text-black hover:bg-orange-400 disabled:opacity-60"
            >
              Create
            </button>
          </form>

          {msg && <p className="text-xs text-orange-400">{msg}</p>}
        </div>
      )}
    </div>
  );
}
