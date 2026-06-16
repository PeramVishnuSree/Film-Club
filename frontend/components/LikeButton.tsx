"use client";

import { useState } from "react";
import { getToken } from "@/lib/api";

/**
 * A heart toggle with a live count. The parent owns the network calls so this
 * stays reusable for both reviews and lists; it just reports the desired next
 * state and optimistically updates while the request is in flight.
 */
export default function LikeButton({
  liked: initialLiked,
  count: initialCount,
  onToggle,
}: {
  liked: boolean;
  count: number;
  onToggle: (next: boolean) => Promise<{ liked: boolean; like_count: number }>;
}) {
  const [liked, setLiked] = useState(initialLiked);
  const [count, setCount] = useState(initialCount);
  const [busy, setBusy] = useState(false);
  const loggedIn = getToken() !== null;

  async function toggle() {
    if (busy || !loggedIn) return;
    const next = !liked;
    // Optimistic update.
    setLiked(next);
    setCount((c) => c + (next ? 1 : -1));
    setBusy(true);
    try {
      const res = await onToggle(next);
      setLiked(res.liked);
      setCount(res.like_count);
    } catch {
      // Roll back on failure.
      setLiked(!next);
      setCount((c) => c + (next ? -1 : 1));
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      onClick={toggle}
      disabled={!loggedIn || busy}
      title={loggedIn ? (liked ? "Unlike" : "Like") : "Log in to like"}
      className={`inline-flex items-center gap-1 text-sm transition-colors ${
        liked ? "text-orange-400" : "text-white/50 hover:text-orange-400"
      } ${!loggedIn ? "cursor-default" : ""}`}
    >
      <span aria-hidden>{liked ? "♥" : "♡"}</span>
      <span>{count}</span>
    </button>
  );
}
