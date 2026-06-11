import Link from "next/link";
import { posterUrl } from "@/lib/api";
import type { FilmSummary } from "@/lib/types";

export default function FilmCard({
  film,
  rank,
}: {
  film: FilmSummary;
  rank?: number;
}) {
  const poster = posterUrl(film.poster_path);
  const year = film.release_date ? film.release_date.slice(0, 4) : "";

  return (
    <Link href={`/film/${film.tmdb_id}`} className="group block">
      <div className="relative aspect-[2/3] overflow-hidden rounded-lg border border-white/10 bg-white/5">
        {poster ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={poster}
            alt={film.title}
            className="h-full w-full object-cover transition group-hover:opacity-80"
          />
        ) : (
          <div className="flex h-full items-center justify-center p-2 text-center text-xs text-white/40">
            {film.title}
          </div>
        )}
        {rank !== undefined && (
          <span className="absolute left-1 top-1 rounded bg-black/70 px-1.5 py-0.5 text-xs font-bold text-emerald-400">
            #{rank}
          </span>
        )}
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
