"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import AddToListButton from "@/components/AddToListButton";
import FilmActions from "@/components/FilmActions";
import ReviewsSection from "@/components/ReviewsSection";
import { api, logoUrl, posterUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { FilmDetail, FilmMeState, Provider } from "@/lib/types";

const OFFER_LABELS: Record<string, string> = {
  flatrate: "Stream",
  rent: "Rent",
  buy: "Buy",
};

function ProviderRow({ label, items }: { label: string; items: Provider[] }) {
  if (items.length === 0) return null;
  return (
    <div className="mb-2">
      <p className="mb-1 text-xs uppercase tracking-wide text-white/50">{label}</p>
      <div className="flex flex-wrap gap-2">
        {items.map((p) => {
          const logo = logoUrl(p.logo_path);
          return (
            <span
              key={`${p.provider_id}-${p.offer_type}`}
              className="flex items-center gap-1.5 rounded bg-white/10 px-2 py-1 text-xs"
              title={p.provider_name}
            >
              {logo && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={logo} alt="" className="h-4 w-4 rounded" />
              )}
              {p.provider_name}
            </span>
          );
        })}
      </div>
    </div>
  );
}

export default function FilmPage() {
  const params = useParams<{ id: string }>();
  const tmdbId = Number(params.id);
  const { user, loading: authLoading } = useAuth();

  const [film, setFilm] = useState<FilmDetail | null>(null);
  const [state, setState] = useState<FilmMeState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reviewKey, setReviewKey] = useState(0);

  useEffect(() => {
    api.film(tmdbId).then(setFilm).catch(() => setError("Could not load this film."));
  }, [tmdbId]);

  useEffect(() => {
    if (user) api.filmState(tmdbId).then(setState).catch(() => setState(null));
  }, [user, tmdbId]);

  if (error) return <p className="text-red-400">{error}</p>;
  if (!film) return <p className="text-white/50">Loading…</p>;

  const poster = posterUrl(film.poster_path, "w342");
  const director = film.crew.find((c) => c.job === "Director");
  const year = film.release_date ? film.release_date.slice(0, 4) : "";
  const providers = {
    flatrate: film.watch_providers.filter((p) => p.offer_type === "flatrate"),
    rent: film.watch_providers.filter((p) => p.offer_type === "rent"),
    buy: film.watch_providers.filter((p) => p.offer_type === "buy"),
  };

  return (
    <div className="grid gap-8 md:grid-cols-[180px_1fr_260px]">
      <div>
        <div className="aspect-[2/3] overflow-hidden rounded-lg border border-white/10 bg-white/5">
          {poster && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={poster} alt={film.title} className="h-full w-full object-cover" />
          )}
        </div>
      </div>

      <div>
        <h1 className="text-2xl font-bold">
          {film.title} {year && <span className="font-normal text-white/50">({year})</span>}
        </h1>
        <p className="mt-1 text-sm text-white/60">
          {director && <>Directed by {director.name} · </>}
          {film.runtime ? `${film.runtime} min` : ""}
          {film.vote_average ? ` · ★ ${film.vote_average.toFixed(1)}` : ""}
        </p>

        <div className="mt-3 flex flex-wrap gap-2">
          {film.genres.map((g) => (
            <span key={g.id} className="rounded-full bg-white/10 px-2.5 py-0.5 text-xs">
              {g.name}
            </span>
          ))}
        </div>

        {film.overview && (
          <p className="mt-4 max-w-prose text-sm leading-relaxed text-white/80">
            {film.overview}
          </p>
        )}

        {film.cast.length > 0 && (
          <div className="mt-4">
            <p className="mb-1 text-xs uppercase tracking-wide text-white/50">Cast</p>
            <p className="text-sm text-white/70">
              {film.cast.slice(0, 8).map((c) => c.name).join(", ")}
            </p>
          </div>
        )}

        <div className="mt-5">
          <p className="mb-1 text-xs uppercase tracking-wide text-white/50">
            Where to watch ({film.region})
          </p>
          {film.watch_providers.length === 0 ? (
            <p className="text-sm text-white/50">Not available on tracked services.</p>
          ) : (
            <>
              <ProviderRow label={OFFER_LABELS.flatrate} items={providers.flatrate} />
              <ProviderRow label={OFFER_LABELS.rent} items={providers.rent} />
              <ProviderRow label={OFFER_LABELS.buy} items={providers.buy} />
            </>
          )}
        </div>

        <div className="mt-8">
          <h2 className="mb-3 text-lg font-semibold">Reviews</h2>
          <ReviewsSection tmdbId={tmdbId} refreshKey={reviewKey} />
        </div>
      </div>

      <aside className="space-y-4">
        {authLoading ? null : user && state ? (
          <>
            <FilmActions
              tmdbId={tmdbId}
              initial={state}
              onReviewed={() => setReviewKey((k) => k + 1)}
            />
            <AddToListButton tmdbId={tmdbId} />
          </>
        ) : (
          <div className="rounded-lg border border-white/10 bg-white/5 p-4 text-sm text-white/60">
            <Link href="/login" className="text-orange-400 hover:underline">
              Log in
            </Link>{" "}
            to rate, log, and review.
          </div>
        )}
      </aside>
    </div>
  );
}
