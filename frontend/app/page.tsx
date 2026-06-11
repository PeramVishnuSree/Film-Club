"use client";

import { useEffect, useState } from "react";
import FilmGrid from "@/components/FilmGrid";
import { api } from "@/lib/api";
import type { FilmSummary } from "@/lib/types";

export default function HomePage() {
  const [films, setFilms] = useState<FilmSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .trending("week")
      .then(setFilms)
      .catch(() => setError("Could not load trending films. Is the backend running?"));
  }, []);

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">Trending this week</h1>
      <p className="mb-6 text-sm text-white/50">Popular films right now on TMDB.</p>
      {error && <p className="text-red-400">{error}</p>}
      {!films && !error && <p className="text-white/50">Loading…</p>}
      {films && <FilmGrid films={films} />}
    </div>
  );
}
