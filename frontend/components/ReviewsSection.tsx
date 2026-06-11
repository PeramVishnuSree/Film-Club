"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Review } from "@/lib/types";

export default function ReviewsSection({
  tmdbId,
  refreshKey,
}: {
  tmdbId: number;
  refreshKey: number;
}) {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [revealed, setRevealed] = useState<Set<number>>(new Set());

  useEffect(() => {
    api.reviews(tmdbId).then(setReviews).catch(() => setReviews([]));
  }, [tmdbId, refreshKey]);

  if (reviews.length === 0) {
    return <p className="text-sm text-white/50">No reviews yet.</p>;
  }

  return (
    <ul className="space-y-4">
      {reviews.map((r) => {
        const hidden = r.contains_spoilers && !revealed.has(r.id);
        return (
          <li key={r.id} className="rounded-lg border border-white/10 bg-white/5 p-4">
            <p className="mb-1 text-sm font-medium">
              {r.author.display_name ?? r.author.username}
            </p>
            {hidden ? (
              <button
                onClick={() => setRevealed((s) => new Set(s).add(r.id))}
                className="text-sm text-amber-400 hover:underline"
              >
                Spoiler — click to reveal
              </button>
            ) : (
              <p className="whitespace-pre-wrap text-sm text-white/80">{r.body}</p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
