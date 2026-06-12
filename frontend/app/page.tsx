"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import FilmGrid from "@/components/FilmGrid";
import { api, posterUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { FilmSummary } from "@/lib/types";

function PosterColumn({
  films,
  direction,
}: {
  films: FilmSummary[];
  direction: "up" | "down";
}) {
  if (films.length === 0) return null;
  // Duplicate the set so the vertical loop is seamless.
  const loop = [...films, ...films];
  return (
    <div className="flex-1">
      <div
        className={direction === "up" ? "animate-scroll-up" : "animate-scroll-down"}
      >
        {loop.map((f, i) => {
          const poster = posterUrl(f.poster_path, "w185");
          return (
            <div
              key={`${f.tmdb_id}-${i}`}
              className="mb-3 aspect-[2/3] overflow-hidden rounded-lg bg-white/5"
            >
              {poster && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={poster} alt="" className="h-full w-full object-cover" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const GUIDE = [
  {
    title: "Discover",
    body: "Browse what's trending and the all-time Top 500.",
    href: "/trending",
    cta: "See trending",
  },
  {
    title: "Log & rate",
    body: "Keep a diary of everything you watch and rate it out of five.",
    href: "/top500",
    cta: "Find a film",
  },
  {
    title: "Review",
    body: "Share your take — with one-click spoiler protection.",
    href: "/top500",
    cta: "Explore",
  },
  {
    title: "Your diary",
    body: "Look back on your watch history any time.",
    href: "/diary",
    cta: "Open diary",
  },
];

export default function HomePage() {
  const { user } = useAuth();
  const [films, setFilms] = useState<FilmSummary[]>([]);

  useEffect(() => {
    let active = true;
    api
      .trending("week")
      .then((data) => {
        if (active) setFilms(data);
      })
      .catch(() => {
        /* hero collage is decorative; ignore failures */
      });
    return () => {
      active = false;
    };
  }, []);

  const withPosters = films.filter((f) => f.poster_path);
  const columns = [
    withPosters.slice(0, 6),
    withPosters.slice(6, 12),
    withPosters.slice(12, 18),
  ];

  return (
    <div className="space-y-14">
      {/* Hero */}
      <section className="relative -mx-4 overflow-hidden rounded-none border-y border-white/10 px-4 py-16 sm:rounded-2xl sm:border">
        {/* Animated poster backdrop */}
        <div
          aria-hidden
          className="poster-fade-mask pointer-events-none absolute inset-0 flex gap-3 opacity-90"
        >
          <PosterColumn films={columns[0]} direction="up" />
          <PosterColumn films={columns[1]} direction="down" />
          <div className="hidden flex-1 sm:block">
            <PosterColumn films={columns[2]} direction="up" />
          </div>
        </div>
        {/* Center vignette: keeps the headline readable while posters stay
            visible toward the edges. */}
        <div
          aria-hidden
          className="absolute inset-0 bg-[radial-gradient(ellipse_70%_60%_at_50%_50%,rgba(10,10,12,0.85),rgba(10,10,12,0.32))]"
        />

        <div className="animate-fade-up relative mx-auto max-w-2xl text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Track films you love.
            <br />
            Find your next watch.
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-white/70">
            Film<span className="text-orange-400">Club</span> is a place to log what
            you watch, rate and review films, build your watchlist, and see where
            everything is streaming.
          </p>
          <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/trending"
              className="rounded-md bg-orange-500 px-5 py-2.5 text-sm font-semibold text-black transition hover:bg-orange-400"
            >
              Browse trending
            </Link>
            <Link
              href="/top500"
              className="rounded-md border border-white/20 px-5 py-2.5 text-sm font-semibold transition hover:bg-white/5"
            >
              Explore the Top 500
            </Link>
            {!user && (
              <Link
                href="/signup"
                className="rounded-md px-5 py-2.5 text-sm font-semibold text-orange-300 transition hover:text-orange-200"
              >
                Sign up free →
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Navigation guide */}
      <section>
        <h2 className="mb-5 text-lg font-semibold">How it works</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {GUIDE.map((g, i) => (
            <Link
              key={g.title}
              href={g.href}
              className="group rounded-xl border border-white/10 bg-white/5 p-5 transition hover:border-orange-400/40 hover:bg-white/[0.07]"
            >
              <span className="text-sm font-bold text-orange-400">
                {String(i + 1).padStart(2, "0")}
              </span>
              <h3 className="mt-2 font-semibold">{g.title}</h3>
              <p className="mt-1 text-sm text-white/60">{g.body}</p>
              <span className="mt-3 inline-block text-sm text-white/50 transition group-hover:text-orange-300">
                {g.cta} →
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* Trending preview */}
      {withPosters.length > 0 && (
        <section>
          <div className="mb-5 flex items-end justify-between">
            <h2 className="text-lg font-semibold">Trending this week</h2>
            <Link
              href="/trending"
              className="text-sm text-orange-400 hover:text-orange-300"
            >
              View all →
            </Link>
          </div>
          <FilmGrid films={withPosters.slice(0, 12)} />
        </section>
      )}
    </div>
  );
}
