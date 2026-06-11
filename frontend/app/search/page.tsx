"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import FilmGrid from "@/components/FilmGrid";
import { api } from "@/lib/api";
import type { FilmSummary } from "@/lib/types";

function SearchResults() {
  const params = useSearchParams();
  const q = params.get("q") ?? "";
  const [films, setFilms] = useState<FilmSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!q) return;
    setFilms(null);
    setError(null);
    api
      .search(q)
      .then(setFilms)
      .catch(() => setError("Search failed."));
  }, [q]);

  if (!q) return <p className="text-white/50">Type a film title in the search box.</p>;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">
        Results for <span className="text-emerald-400">{q}</span>
      </h1>
      {error && <p className="text-red-400">{error}</p>}
      {!films && !error && <p className="text-white/50">Searching…</p>}
      {films && films.length === 0 && <p className="text-white/50">No films found.</p>}
      {films && films.length > 0 && <FilmGrid films={films} />}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<p className="text-white/50">Loading…</p>}>
      <SearchResults />
    </Suspense>
  );
}
