"use client";

import { useEffect, useState } from "react";
import FilmGrid from "@/components/FilmGrid";
import { api } from "@/lib/api";
import type { FilmSummary } from "@/lib/types";

type Window = "day" | "week";

export default function TrendingPage() {
  const [window, setWindow] = useState<Window>("week");
  // Tag the result with the window it belongs to so we can derive loading
  // state without resetting state synchronously inside the effect.
  const [result, setResult] = useState<{ window: Window; films: FilmSummary[] } | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .trending(window)
      .then((films) => {
        if (active) {
          setResult({ window, films });
          setError(null);
        }
      })
      .catch(() => {
        if (active) setError("Could not load trending films. Is the backend running?");
      });
    return () => {
      active = false;
    };
  }, [window]);

  const films = result && result.window === window ? result.films : null;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="mb-1 text-2xl font-bold">Trending</h1>
          <p className="text-sm text-white/50">Popular films right now on TMDB.</p>
        </div>
        <div className="flex rounded-md border border-white/15 p-0.5 text-sm">
          {(["day", "week"] as const).map((w) => (
            <button
              key={w}
              onClick={() => setWindow(w)}
              className={`rounded px-3 py-1 capitalize transition ${
                window === w
                  ? "bg-orange-500 font-medium text-black"
                  : "text-white/70 hover:text-white"
              }`}
            >
              {w === "day" ? "Today" : "This week"}
            </button>
          ))}
        </div>
      </div>
      {error && <p className="text-red-400">{error}</p>}
      {!films && !error && <p className="text-white/50">Loading…</p>}
      {films && <FilmGrid films={films} />}
    </div>
  );
}
