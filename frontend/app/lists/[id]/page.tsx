"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError, posterUrl } from "@/lib/api";
import type { FilmSummary, ListDetail } from "@/lib/types";

export default function ListDetailPage() {
  const { id } = useParams<{ id: string }>();
  const listId = Number(id);
  const router = useRouter();

  const [list, setList] = useState<ListDetail | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (!listId) return;
    let active = true;
    api
      .list(listId)
      .then((l) => active && setList(l))
      .catch((e) => {
        if (active && e instanceof ApiError && e.status === 404) setNotFound(true);
      });
    return () => {
      active = false;
    };
  }, [listId]);

  if (notFound) {
    return (
      <div>
        <h1 className="text-2xl font-bold">List not found</h1>
        <p className="mt-2 text-white/50">
          It may be private or deleted.{" "}
          <Link href="/lists" className="text-orange-400 hover:underline">
            Your lists
          </Link>
        </p>
      </div>
    );
  }

  if (!list) return <p className="text-white/50">Loading…</p>;

  async function reload() {
    setList(await api.list(listId));
  }

  async function move(tmdbId: number, dir: -1 | 1) {
    if (!list) return;
    const order = list.items.map((i) => i.film.tmdb_id);
    const idx = order.indexOf(tmdbId);
    const swap = idx + dir;
    if (swap < 0 || swap >= order.length) return;
    [order[idx], order[swap]] = [order[swap], order[idx]];
    setList({ ...list, items: order.map((t) => list.items.find((i) => i.film.tmdb_id === t)!) });
    await api.reorderList(listId, order);
    await reload();
  }

  async function remove(tmdbId: number) {
    if (!list) return;
    setList({
      ...list,
      items: list.items.filter((i) => i.film.tmdb_id !== tmdbId),
      item_count: list.item_count - 1,
    });
    await api.removeListItem(listId, tmdbId);
    await reload();
  }

  async function deleteList() {
    if (!confirm(`Delete “${list?.title}”? This can't be undone.`)) return;
    await api.deleteList(listId);
    router.push("/lists");
  }

  const owner = list.owner;

  return (
    <div>
      <div className="mb-1 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{list.title}</h1>
          <p className="mt-1 text-sm text-white/50">
            {list.item_count} {list.item_count === 1 ? "film" : "films"}
            {list.is_ranked && " · ranked"}
            {!list.is_public && " · private"}
            {owner && (
              <>
                {" · by "}
                <Link
                  href={`/u/${owner.username}`}
                  className="text-white/70 hover:text-orange-400"
                >
                  {owner.display_name ?? owner.username}
                </Link>
              </>
            )}
          </p>
        </div>
        {list.is_owner && (
          <div className="flex shrink-0 gap-2">
            <button
              onClick={() => setEditing((e) => !e)}
              className="rounded-md border border-white/15 px-3 py-1.5 text-sm text-white/80 hover:border-white/40"
            >
              {editing ? "Done" : "Edit"}
            </button>
            <button
              onClick={deleteList}
              className="rounded-md border border-red-500/40 px-3 py-1.5 text-sm text-red-400 hover:border-red-500"
            >
              Delete
            </button>
          </div>
        )}
      </div>

      {list.description && (
        <p className="mb-5 max-w-prose text-sm text-white/70">{list.description}</p>
      )}

      {list.is_owner && editing && (
        <EditPanel list={list} onSaved={reload} />
      )}
      {list.is_owner && <AddFilm listId={listId} onAdded={reload} />}

      {list.items.length === 0 ? (
        <p className="text-white/50">No films yet.</p>
      ) : (
        <ol className="space-y-2">
          {list.items.map((item, idx) => (
            <li
              key={item.film.tmdb_id}
              className="flex items-center gap-3 rounded-lg border border-white/10 bg-white/[0.03] p-2"
            >
              {list.is_ranked && (
                <span className="w-6 shrink-0 text-center text-sm font-bold text-orange-400">
                  {item.rank ?? idx + 1}
                </span>
              )}
              <Link href={`/film/${item.film.tmdb_id}`} className="shrink-0">
                {item.film.poster_path ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={posterUrl(item.film.poster_path, "w92") ?? ""}
                    alt={item.film.title}
                    className="h-16 w-11 rounded object-cover"
                  />
                ) : (
                  <div className="flex h-16 w-11 items-center justify-center rounded bg-white/10 text-[10px] text-white/40">
                    ?
                  </div>
                )}
              </Link>
              <div className="min-w-0 flex-1">
                <Link
                  href={`/film/${item.film.tmdb_id}`}
                  className="font-medium hover:text-orange-400"
                >
                  {item.film.title}
                </Link>
                {item.film.release_date && (
                  <span className="ml-2 text-xs text-white/40">
                    {item.film.release_date.slice(0, 4)}
                  </span>
                )}
                {item.note && (
                  <p className="mt-0.5 text-sm text-white/60">{item.note}</p>
                )}
              </div>
              {list.is_owner && editing && (
                <div className="flex shrink-0 items-center gap-1">
                  {list.is_ranked && (
                    <>
                      <button
                        onClick={() => move(item.film.tmdb_id, -1)}
                        disabled={idx === 0}
                        className="rounded px-2 py-1 text-white/50 hover:bg-white/10 hover:text-white disabled:opacity-30"
                        aria-label="Move up"
                      >
                        ↑
                      </button>
                      <button
                        onClick={() => move(item.film.tmdb_id, 1)}
                        disabled={idx === list.items.length - 1}
                        className="rounded px-2 py-1 text-white/50 hover:bg-white/10 hover:text-white disabled:opacity-30"
                        aria-label="Move down"
                      >
                        ↓
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => remove(item.film.tmdb_id)}
                    className="rounded px-2 py-1 text-red-400 hover:bg-red-500/10"
                    aria-label="Remove"
                  >
                    ✕
                  </button>
                </div>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

// ----- metadata editor
function EditPanel({
  list,
  onSaved,
}: {
  list: ListDetail;
  onSaved: () => Promise<void>;
}) {
  const [title, setTitle] = useState(list.title);
  const [description, setDescription] = useState(list.description ?? "");
  const [isRanked, setIsRanked] = useState(list.is_ranked);
  const [isPublic, setIsPublic] = useState(list.is_public);
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    try {
      await api.updateList(list.id, {
        title: title.trim() || list.title,
        description: description.trim() || null,
        is_ranked: isRanked,
        is_public: isPublic,
      });
      await onSaved();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mb-5 space-y-3 rounded-lg border border-white/10 bg-white/[0.03] p-4">
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        maxLength={200}
        className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 text-sm outline-none focus:border-orange-400"
      />
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        maxLength={2000}
        rows={2}
        placeholder="Description"
        className="w-full resize-y rounded-md border border-white/15 bg-white/5 px-3 py-2 text-sm outline-none focus:border-orange-400"
      />
      <div className="flex items-center gap-6 text-sm">
        <label className="flex items-center gap-2 text-white/70">
          <input
            type="checkbox"
            checked={isRanked}
            onChange={(e) => setIsRanked(e.target.checked)}
            className="accent-orange-500"
          />
          Ranked
        </label>
        <label className="flex items-center gap-2 text-white/70">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
            className="accent-orange-500"
          />
          Public
        </label>
        <button
          onClick={save}
          disabled={busy}
          className="ml-auto rounded-md bg-orange-500 px-4 py-1.5 text-sm font-medium text-black hover:bg-orange-400 disabled:opacity-60"
        >
          {busy ? "Saving…" : "Save"}
        </button>
      </div>
    </div>
  );
}

// ----- add film via search
function AddFilm({
  listId,
  onAdded,
}: {
  listId: number;
  onAdded: () => Promise<void>;
}) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<FilmSummary[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    setSearching(true);
    setError(null);
    try {
      setResults(await api.search(q.trim()));
    } finally {
      setSearching(false);
    }
  }

  async function add(film: FilmSummary) {
    setError(null);
    try {
      await api.addListItem(listId, film.tmdb_id);
      setResults((r) => r.filter((f) => f.tmdb_id !== film.tmdb_id));
      await onAdded();
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 409
          ? `“${film.title}” is already in this list.`
          : "Could not add film.",
      );
    }
  }

  return (
    <div className="mb-5 rounded-lg border border-white/10 bg-white/[0.03] p-3">
      <form onSubmit={search} className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search films to add…"
          className="flex-1 rounded-md border border-white/15 bg-white/5 px-3 py-2 text-sm outline-none focus:border-orange-400"
        />
        <button
          type="submit"
          disabled={searching}
          className="rounded-md border border-white/15 px-4 py-2 text-sm text-white/80 hover:border-white/40 disabled:opacity-60"
        >
          {searching ? "…" : "Search"}
        </button>
      </form>
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      {results.length > 0 && (
        <ul className="mt-3 max-h-72 space-y-1 overflow-y-auto">
          {results.slice(0, 12).map((film) => (
            <li
              key={film.tmdb_id}
              className="flex items-center gap-3 rounded-md px-2 py-1.5 hover:bg-white/5"
            >
              {film.poster_path ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={posterUrl(film.poster_path, "w92") ?? ""}
                  alt=""
                  className="h-12 w-8 rounded object-cover"
                />
              ) : (
                <div className="h-12 w-8 rounded bg-white/10" />
              )}
              <span className="min-w-0 flex-1 truncate text-sm">
                {film.title}
                {film.release_date && (
                  <span className="ml-1 text-white/40">
                    {film.release_date.slice(0, 4)}
                  </span>
                )}
              </span>
              <button
                onClick={() => add(film)}
                className="rounded-md bg-orange-500 px-3 py-1 text-xs font-medium text-black hover:bg-orange-400"
              >
                Add
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
