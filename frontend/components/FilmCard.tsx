"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { api, logoUrl, posterUrl } from "@/lib/api";
import type { FilmSummary, Provider } from "@/lib/types";

// Module-level cache so each film's providers are fetched at most once per session.
const providerCache = new Map<number, Promise<Provider[]>>();

function loadProviders(tmdbId: number): Promise<Provider[]> {
  let cached = providerCache.get(tmdbId);
  if (!cached) {
    cached = api.filmProviders(tmdbId).catch(() => [] as Provider[]);
    providerCache.set(tmdbId, cached);
  }
  return cached;
}

export default function FilmCard({
  film,
  rank,
}: {
  film: FilmSummary;
  rank?: number;
}) {
  const poster = posterUrl(film.poster_path);
  const year = film.release_date ? film.release_date.slice(0, 4) : "";

  const [providers, setProviders] = useState<Provider[] | null>(null);
  const hoverTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function onEnter() {
    if (providers !== null) return;
    hoverTimer.current = setTimeout(() => {
      loadProviders(film.tmdb_id).then(setProviders);
    }, 120);
  }
  function onLeave() {
    if (hoverTimer.current) clearTimeout(hoverTimer.current);
  }

  const streaming = providers?.filter((p) => p.offer_type === "flatrate") ?? [];

  return (
    <Link
      href={`/film/${film.tmdb_id}`}
      className="group block"
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
    >
      <div className="relative aspect-[2/3] overflow-hidden rounded-lg border border-white/10 bg-white/5">
        {poster ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={poster}
            alt={film.title}
            className="h-full w-full object-cover transition duration-300 group-hover:scale-105 group-hover:opacity-90"
          />
        ) : (
          <div className="flex h-full items-center justify-center p-2 text-center text-xs text-white/40">
            {film.title}
          </div>
        )}
        {rank !== undefined && (
          <span className="absolute left-1 top-1 rounded bg-black/70 px-1.5 py-0.5 text-xs font-bold text-orange-400">
            #{rank}
          </span>
        )}

        {/* Streaming providers — revealed on hover. */}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 translate-y-2 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-2 opacity-0 transition duration-300 group-hover:translate-y-0 group-hover:opacity-100">
          {providers === null ? (
            <p className="text-[10px] text-white/50">Loading…</p>
          ) : streaming.length > 0 ? (
            <>
              <p className="mb-1 text-[10px] uppercase tracking-wide text-white/60">
                Streaming
              </p>
              <div className="flex flex-wrap gap-1">
                {streaming.slice(0, 4).map((p) => {
                  const logo = logoUrl(p.logo_path);
                  return logo ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      key={p.provider_id}
                      src={logo}
                      alt={p.provider_name}
                      title={p.provider_name}
                      className="h-6 w-6 rounded"
                    />
                  ) : (
                    <span
                      key={p.provider_id}
                      className="rounded bg-white/15 px-1 text-[10px]"
                      title={p.provider_name}
                    >
                      {p.provider_name}
                    </span>
                  );
                })}
              </div>
            </>
          ) : (
            <p className="text-[10px] text-white/50">Not streaming</p>
          )}
        </div>
      </div>
      <div className="mt-1.5">
        <p className="truncate text-sm font-medium" title={film.title}>
          {film.title}
        </p>
        <p className="text-xs text-white/50">
          {year}
          {film.vote_average ? ` · ★ ${film.vote_average.toFixed(1)}` : ""}
        </p>
      </div>
    </Link>
  );
}
