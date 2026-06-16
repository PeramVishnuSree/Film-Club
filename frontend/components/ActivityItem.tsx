import Link from "next/link";
import { posterUrl } from "@/lib/api";
import type { FeedItem } from "@/lib/types";

// Human-readable verb for each interaction type.
function describe(item: FeedItem): string {
  switch (item.type) {
    case "rate":
      return item.value != null ? `rated ★${item.value}` : "rated";
    case "log":
      return "logged";
    case "review":
      return "reviewed";
    case "watchlist_add":
      return "added to watchlist";
    case "like":
      return "liked";
    case "list_add":
      return "added to a list";
    default:
      return item.type;
  }
}

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  const secs = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (secs < 60) return "just now";
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

export default function ActivityItem({ item }: { item: FeedItem }) {
  const actor = item.actor;
  const poster = posterUrl(item.film.poster_path, "w92");
  return (
    <div className="flex items-center gap-3 rounded-lg border border-white/10 bg-white/[0.03] p-3">
      <Link href={`/film/${item.film.tmdb_id}`} className="shrink-0">
        {poster ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={poster}
            alt={item.film.title}
            className="h-16 w-11 rounded object-cover"
          />
        ) : (
          <div className="flex h-16 w-11 items-center justify-center rounded bg-white/10 text-[10px] text-white/40">
            ?
          </div>
        )}
      </Link>
      <div className="min-w-0 text-sm">
        <p className="text-white/80">
          <Link
            href={`/u/${actor.username}`}
            className="font-medium text-white hover:text-orange-400"
          >
            {actor.display_name ?? actor.username}
          </Link>{" "}
          {describe(item)}{" "}
          <Link
            href={`/film/${item.film.tmdb_id}`}
            className="font-medium text-white hover:text-orange-400"
          >
            {item.film.title}
          </Link>
        </p>
        <p className="mt-0.5 text-xs text-white/40">{timeAgo(item.created_at)}</p>
      </div>
    </div>
  );
}
