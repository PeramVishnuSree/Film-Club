"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import FilmGrid from "@/components/FilmGrid";
import UserCardRow from "@/components/UserCardRow";
import { api } from "@/lib/api";
import type { FilmSummary, UserCard } from "@/lib/types";

function SearchResults() {
  const params = useSearchParams();
  const q = params.get("q") ?? "";
  // Tag results with their query so loading state is derived rather than
  // reset synchronously inside the effect.
  const [result, setResult] = useState<{
    q: string;
    films: FilmSummary[];
    people: UserCard[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!q) return;
    let active = true;
    Promise.all([api.search(q), api.searchUsers(q).catch(() => [])])
      .then(([films, people]) => {
        if (active) {
          setResult({ q, films, people });
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

  const data = result && result.q === q ? result : null;

  if (!q) return <p className="text-white/50">Type a film title or name in the search box.</p>;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">
        Results for <span className="text-orange-400">{q}</span>
      </h1>
      {error && <p className="text-red-400">{error}</p>}
      {!data && !error && <p className="text-white/50">Searching…</p>}

      {data && data.people.length > 0 && (
        <div className="mb-8">
          <h2 className="mb-3 text-lg font-semibold">People</h2>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {data.people.map((u) => (
              <UserCardRow key={u.id} user={u} />
            ))}
          </div>
        </div>
      )}

      {data && (
        <div>
          {data.people.length > 0 && (
            <h2 className="mb-3 text-lg font-semibold">Films</h2>
          )}
          {data.films.length === 0 ? (
            <p className="text-white/50">No films found.</p>
          ) : (
            <FilmGrid films={data.films} />
          )}
        </div>
      )}
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
