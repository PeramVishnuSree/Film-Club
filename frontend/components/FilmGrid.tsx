import FilmCard from "./FilmCard";
import type { FilmSummary, RankedFilm } from "@/lib/types";

export default function FilmGrid({ films }: { films: (FilmSummary | RankedFilm)[] }) {
  return (
    <div className="grid grid-cols-3 gap-4 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6">
      {films.map((film) => (
        <FilmCard
          key={film.tmdb_id}
          film={film}
          rank={"rank" in film ? film.rank : undefined}
        />
      ))}
    </div>
  );
}
