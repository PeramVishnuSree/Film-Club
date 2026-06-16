"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import ActivityItem from "@/components/ActivityItem";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { FeedItem } from "@/lib/types";

const PAGE_SIZE = 30;

export default function FeedPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<FeedItem[] | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (user)
      api
        .myFeed(PAGE_SIZE, 0)
        .then((page) => {
          setItems(page);
          setHasMore(page.length === PAGE_SIZE);
        })
        .catch(() => setItems([]));
  }, [user]);

  async function loadMore() {
    if (!items || loadingMore) return;
    setLoadingMore(true);
    try {
      const page = await api.myFeed(PAGE_SIZE, items.length);
      setItems([...items, ...page]);
      setHasMore(page.length === PAGE_SIZE);
    } finally {
      setLoadingMore(false);
    }
  }

  if (loading || !user) return <p className="text-white/50">Loading…</p>;

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">Your feed</h1>
      <p className="mb-6 text-sm text-white/50">
        Recent activity from people you follow.
      </p>
      {!items && <p className="text-white/50">Loading…</p>}
      {items && items.length === 0 && (
        <p className="text-white/50">
          Quiet in here. Follow some people to see their activity — start by{" "}
          <Link href="/top500" className="text-orange-400 hover:underline">
            browsing films
          </Link>{" "}
          and checking out reviewers.
        </p>
      )}
      {items && items.length > 0 && (
        <div className="space-y-2">
          {items.map((item) => (
            <ActivityItem key={item.id} item={item} />
          ))}
        </div>
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
