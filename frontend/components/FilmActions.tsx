"use client";

import { useState } from "react";
import StarRating from "./StarRating";
import { api } from "@/lib/api";
import type { FilmMeState } from "@/lib/types";

export default function FilmActions({
  tmdbId,
  initial,
  onReviewed,
}: {
  tmdbId: number;
  initial: FilmMeState;
  onReviewed?: () => void;
}) {
  const [state, setState] = useState<FilmMeState>(initial);
  const [showLog, setShowLog] = useState(false);
  const [logForm, setLogForm] = useState({
    watched_on: new Date().toISOString().slice(0, 10),
    liked: false,
    rewatch: false,
    note: "",
  });
  const [reviewBody, setReviewBody] = useState("");
  const [spoilers, setSpoilers] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function rate(value: number) {
    setState((s) => ({ ...s, rating: value }));
    await api.setRating(tmdbId, value);
  }
  async function clearRating() {
    setState((s) => ({ ...s, rating: null }));
    await api.deleteRating(tmdbId);
  }
  async function toggleWatchlist() {
    if (state.watchlisted) {
      setState((s) => ({ ...s, watchlisted: false }));
      await api.removeWatchlist(tmdbId);
    } else {
      setState((s) => ({ ...s, watchlisted: true }));
      await api.addWatchlist(tmdbId);
    }
  }
  async function submitLog(e: React.FormEvent) {
    e.preventDefault();
    await api.addDiary(tmdbId, {
      watched_on: logForm.watched_on,
      liked: logForm.liked,
      rewatch: logForm.rewatch,
      note: logForm.note || null,
    });
    setState((s) => ({ ...s, watched: true }));
    setShowLog(false);
    setMsg("Logged to your diary.");
  }
  async function submitReview(e: React.FormEvent) {
    e.preventDefault();
    if (!reviewBody.trim()) return;
    await api.addReview(tmdbId, { body: reviewBody, contains_spoilers: spoilers });
    setReviewBody("");
    setSpoilers(false);
    setMsg("Review posted.");
    onReviewed?.();
  }

  return (
    <div className="space-y-4 rounded-lg border border-white/10 bg-white/5 p-4">
      <div>
        <p className="mb-1 text-xs uppercase tracking-wide text-white/50">Your rating</p>
        <div className="flex items-center gap-3">
          <StarRating value={state.rating} onChange={rate} />
          {state.rating != null && (
            <button onClick={clearRating} className="text-xs text-white/40 hover:text-white">
              clear
            </button>
          )}
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={toggleWatchlist}
          className={`flex-1 rounded-md px-3 py-2 text-sm font-medium ${
            state.watchlisted
              ? "bg-emerald-500/20 text-emerald-300"
              : "border border-white/15 hover:bg-white/5"
          }`}
        >
          {state.watchlisted ? "✓ Watchlist" : "+ Watchlist"}
        </button>
        <button
          onClick={() => setShowLog((v) => !v)}
          className="flex-1 rounded-md border border-white/15 px-3 py-2 text-sm font-medium hover:bg-white/5"
        >
          {state.watched ? "Log again" : "Log"}
        </button>
      </div>

      {showLog && (
        <form onSubmit={submitLog} className="space-y-2 rounded-md bg-black/30 p-3">
          <input
            type="date"
            value={logForm.watched_on}
            onChange={(e) => setLogForm((f) => ({ ...f, watched_on: e.target.value }))}
            className="w-full rounded border border-white/15 bg-white/5 px-2 py-1 text-sm"
          />
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={logForm.liked}
              onChange={(e) => setLogForm((f) => ({ ...f, liked: e.target.checked }))}
            />
            Liked
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={logForm.rewatch}
              onChange={(e) => setLogForm((f) => ({ ...f, rewatch: e.target.checked }))}
            />
            Rewatch
          </label>
          <textarea
            value={logForm.note}
            onChange={(e) => setLogForm((f) => ({ ...f, note: e.target.value }))}
            placeholder="Notes (optional)"
            className="w-full rounded border border-white/15 bg-white/5 px-2 py-1 text-sm"
            rows={2}
          />
          <button className="w-full rounded bg-emerald-500 px-3 py-1.5 text-sm font-medium text-black hover:bg-emerald-400">
            Save entry
          </button>
        </form>
      )}

      <form onSubmit={submitReview} className="space-y-2">
        <p className="text-xs uppercase tracking-wide text-white/50">Write a review</p>
        <textarea
          value={reviewBody}
          onChange={(e) => setReviewBody(e.target.value)}
          placeholder="Your thoughts…"
          className="w-full rounded border border-white/15 bg-white/5 px-2 py-1 text-sm"
          rows={3}
        />
        <label className="flex items-center gap-2 text-xs text-white/60">
          <input
            type="checkbox"
            checked={spoilers}
            onChange={(e) => setSpoilers(e.target.checked)}
          />
          Contains spoilers
        </label>
        <button className="w-full rounded border border-white/15 px-3 py-1.5 text-sm font-medium hover:bg-white/5">
          Post review
        </button>
      </form>

      {msg && <p className="text-xs text-emerald-400">{msg}</p>}
    </div>
  );
}
