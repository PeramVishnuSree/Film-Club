"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, posterUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { DiaryEntry } from "@/lib/types";

export default function DiaryPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [entries, setEntries] = useState<DiaryEntry[] | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (user) api.myDiary().then(setEntries).catch(() => setEntries([]));
  }, [user]);

  if (loading || !user) return <p className="text-white/50">Loading…</p>;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Your diary</h1>
      {!entries && <p className="text-white/50">Loading…</p>}
      {entries && entries.length === 0 && (
        <p className="text-white/50">
          Nothing logged yet. Find a film and hit “Log”.
        </p>
      )}
      <ul className="space-y-3">
        {entries?.map((e) => {
          const poster = posterUrl(e.poster_path, "w92");
          return (
            <li
              key={e.id}
              className="flex items-center gap-3 rounded-lg border border-white/10 bg-white/5 p-3"
            >
              <Link href={`/film/${e.film_tmdb_id}`} className="shrink-0">
                <div className="h-16 w-11 overflow-hidden rounded bg-white/10">
                  {poster && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={poster} alt="" className="h-full w-full object-cover" />
                  )}
                </div>
              </Link>
              <div className="min-w-0 flex-1">
                <Link
                  href={`/film/${e.film_tmdb_id}`}
                  className="font-medium hover:text-orange-400"
                >
                  {e.film_title}
                </Link>
                <p className="text-xs text-white/50">
                  Watched {e.watched_on}
                  {e.rewatch && " · rewatch"}
                  {e.liked && " · ♥"}
                  {e.rating_value != null && ` · ★ ${e.rating_value}`}
                </p>
                {e.note && <p className="mt-1 text-sm text-white/70">{e.note}</p>}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
