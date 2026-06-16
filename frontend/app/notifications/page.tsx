"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Notification } from "@/lib/types";

const PAGE_SIZE = 30;

function timeAgo(iso: string): string {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return "just now";
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

function NotificationRow({ n }: { n: Notification }) {
  const actorName = n.actor
    ? n.actor.display_name ?? n.actor.username
    : "Someone";
  const actorLink = n.actor ? (
    <Link href={`/u/${n.actor.username}`} className="font-medium hover:text-orange-400">
      {actorName}
    </Link>
  ) : (
    <span className="font-medium">{actorName}</span>
  );

  let body: React.ReactNode;
  if (n.type === "follow") {
    body = <>started following you.</>;
  } else if (n.type === "review_like") {
    const film = n.data?.film_title;
    const tmdbId = n.data?.film_tmdb_id;
    body = (
      <>
        liked your review
        {film && tmdbId ? (
          <>
            {" "}of{" "}
            <Link href={`/film/${tmdbId}`} className="hover:text-orange-400">
              {film}
            </Link>
          </>
        ) : null}
        .
      </>
    );
  } else if (n.type === "list_like") {
    const title = n.data?.list_title;
    const listId = n.data?.list_id;
    body = (
      <>
        liked your list
        {title && listId ? (
          <>
            {" "}
            <Link href={`/lists/${listId}`} className="hover:text-orange-400">
              “{title}”
            </Link>
          </>
        ) : null}
        .
      </>
    );
  } else {
    body = <>{n.type}</>;
  }

  return (
    <li
      className={`flex items-start justify-between gap-3 rounded-lg border p-3 ${
        n.read
          ? "border-white/10 bg-white/[0.02]"
          : "border-orange-500/30 bg-orange-500/[0.06]"
      }`}
    >
      <p className="text-sm text-white/80">
        {actorLink} {body}
      </p>
      <span className="shrink-0 text-xs text-white/40">
        {timeAgo(n.created_at)}
      </span>
    </li>
  );
}

export default function NotificationsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Notification[] | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (!user) return;
    api
      .notifications(PAGE_SIZE, 0)
      .then((page) => {
        setItems(page);
        setHasMore(page.length === PAGE_SIZE);
      })
      .catch(() => setItems([]));
    // Opening the page clears the unread badge.
    api.markNotificationsRead().catch(() => {});
  }, [user]);

  async function loadMore() {
    if (!items || loadingMore) return;
    setLoadingMore(true);
    try {
      const page = await api.notifications(PAGE_SIZE, items.length);
      setItems([...items, ...page]);
      setHasMore(page.length === PAGE_SIZE);
    } finally {
      setLoadingMore(false);
    }
  }

  if (loading || !user) return <p className="text-white/50">Loading…</p>;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Notifications</h1>
      {!items && <p className="text-white/50">Loading…</p>}
      {items && items.length === 0 && (
        <p className="text-white/50">
          Nothing yet. When people follow you or like your reviews and lists,
          you’ll see it here.
        </p>
      )}
      {items && items.length > 0 && (
        <ul className="space-y-2">
          {items.map((n) => (
            <NotificationRow key={n.id} n={n} />
          ))}
        </ul>
      )}
      {items && items.length > 0 && hasMore && (
        <div className="mt-4 text-center">
          <button
            onClick={loadMore}
            disabled={loadingMore}
            className="rounded-md border border-white/15 px-4 py-2 text-sm text-white/70 hover:border-white/40 hover:text-white disabled:opacity-60"
          >
            {loadingMore ? "Loading…" : "Load more"}
          </button>
        </div>
      )}
    </div>
  );
}
