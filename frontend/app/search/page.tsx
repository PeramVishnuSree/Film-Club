"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import FilmGrid from "@/components/FilmGrid";
import { api } from "@/lib/api";
import type { FilmSummary } from "@/lib/types";

function SearchResults() {
  const params = useSearchParams();
  const q = params.get("q") ?? "";
  // Tag results with their query so loading state is derived rather than
  // reset synchronously inside the effect.
  const [result, setResult] = useState<{ q: string; films: FilmSummary[] } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!q) return;
    let active = true;
    api
      .search(q)
      .then((films) => {
        if (active) {
          setResult({ q, films });
          setError(null);
        }
      })
      .catch(() => {
        if (active) setError("Search failed.");
      });
    return () => {
      active = false;
    };
  }, [q]);

  const films = result && result.q === q ? result.films : null;

  if (!q) return <p className="text-white/50">Type a film title in the search box.</p>;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">
        Results for <span className="text-orange-400">{q}</span>
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
