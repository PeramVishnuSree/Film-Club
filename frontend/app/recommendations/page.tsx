"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import FilmCard from "@/components/FilmCard";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { RecommendedFilm } from "@/lib/types";

export default function RecommendationsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [films, setFilms] = useState<RecommendedFilm[] | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (user)
      api
        .recommendations(24)
        .then(setFilms)
        .catch(() => setFilms([]));
  }, [user]);

  if (loading || !user) return <p className="text-white/50">Loading…</p>;

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">For you</h1>
      <p className="mb-6 text-sm text-white/50">
        Picks from the people you follow, topped up with popular films.
      </p>
      {!films && <p className="text-white/50">Loading…</p>}
      {films && films.length === 0 && (
        <p className="text-white/50">
          No recommendations yet — follow some people and log a few films to
          warm things up.
        </p>
      )}
      {films && films.length > 0 && (
        <div className="grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {films.map((film) => (
            <div key={film.tmdb_id}>
              <FilmCard film={film} />
              <p className="mt-1 line-clamp-2 text-xs text-orange-400/80">
                {film.reason}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
