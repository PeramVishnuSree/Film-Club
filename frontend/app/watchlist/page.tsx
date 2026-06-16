"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import FilmGrid from "@/components/FilmGrid";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { FilmSummary } from "@/lib/types";

export default function WatchlistPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [films, setFilms] = useState<FilmSummary[] | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (user) api.myWatchlist().then(setFilms).catch(() => setFilms([]));
  }, [user]);

  if (loading || !user) return <p className="text-white/50">Loading…</p>;

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">Your watchlist</h1>
      <p className="mb-6 text-sm text-white/50">Films you want to watch.</p>
      {!films && <p className="text-white/50">Loading…</p>}
      {films && films.length === 0 && (
        <p className="text-white/50">
          Nothing here yet. Find a film and hit{" "}
          <Link href="/trending" className="text-orange-400 hover:underline">
            + Watchlist
          </Link>
          .
        </p>
      )}
      {films && films.length > 0 && <FilmGrid films={films} />}
    </div>
  );
}
