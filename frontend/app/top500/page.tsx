"use client";

import { useEffect, useState } from "react";
import FilmGrid from "@/components/FilmGrid";
import { api } from "@/lib/api";
import type { RankedFilm } from "@/lib/types";

const PAGE_SIZE = 60;

export default function Top500Page() {
  const [films, setFilms] = useState<RankedFilm[]>([]);
  const [offset, setOffset] = useState(0);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api
      .top500(PAGE_SIZE, offset)
      .then((batch) => {
        setFilms((prev) => [...prev, ...batch]);
        if (batch.length < PAGE_SIZE) setDone(true);
      })
      .catch(() => setError("Could not load the Top 500."))
      .finally(() => setLoading(false));
  }, [offset]);

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">Top 500</h1>
      <p className="mb-6 text-sm text-white/50">
        The highest-rated films, ranked from TMDB ratings.
      </p>
      {error && <p className="text-red-400">{error}</p>}
      {films.length === 0 && !error && (
        <p className="text-white/50">
          {loading ? "Loading…" : "The Top 500 hasn't been generated yet."}
        </p>
      )}
      <FilmGrid films={films} />
      {!done && films.length > 0 && (
        <div className="mt-6 flex justify-center">
          <button
            disabled={loading}
            onClick={() => setOffset((o) => o + PAGE_SIZE)}
            className="rounded-md border border-white/15 px-4 py-2 text-sm hover:bg-white/5 disabled:opacity-50"
          >
            {loading ? "Loading…" : "Load more"}
          </button>
        </div>
      )}
    </div>
  );
}
