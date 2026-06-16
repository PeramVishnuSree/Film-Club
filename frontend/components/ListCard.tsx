import Link from "next/link";
import { posterUrl } from "@/lib/api";
import type { ListSummary } from "@/lib/types";

export default function ListCard({ list }: { list: ListSummary }) {
  const posters = list.preview_posters.slice(0, 5);
  return (
    <Link
      href={`/lists/${list.id}`}
      className="block rounded-lg border border-white/10 bg-white/[0.03] p-4 hover:border-white/20"
    >
      <div className="mb-3 flex -space-x-6">
        {posters.length > 0 ? (
          posters.map((p, i) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              key={i}
              src={posterUrl(p, "w92") ?? ""}
              alt=""
              className="h-24 w-16 rounded border border-black/40 object-cover shadow-md"
              style={{ zIndex: posters.length - i }}
            />
          ))
        ) : (
          <div className="flex h-24 w-full items-center justify-center rounded bg-white/5 text-sm text-white/30">
            Empty list
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        <h3 className="truncate font-semibold">{list.title}</h3>
        {list.is_ranked && (
          <span className="rounded bg-orange-500/20 px-1.5 py-0.5 text-[10px] font-medium text-orange-400">
            RANKED
          </span>
        )}
        {!list.is_public && (
          <span className="rounded bg-white/10 px-1.5 py-0.5 text-[10px] text-white/50">
            PRIVATE
          </span>
        )}
      </div>
      <p className="mt-0.5 text-xs text-white/40">
        {list.item_count} {list.item_count === 1 ? "film" : "films"}
        {list.owner ? ` · ${list.owner.display_name ?? list.owner.username}` : ""}
      </p>
      {list.description && (
        <p className="mt-1 line-clamp-2 text-sm text-white/60">{list.description}</p>
      )}
    </Link>
  );
}
