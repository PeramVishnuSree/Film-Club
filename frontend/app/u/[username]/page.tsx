"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ActivityItem from "@/components/ActivityItem";
import FollowButton from "@/components/FollowButton";
import ListCard from "@/components/ListCard";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { FeedItem, ListSummary, Profile } from "@/lib/types";

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <div className="text-lg font-bold">{value}</div>
      <div className="text-xs uppercase tracking-wide text-white/40">{label}</div>
    </div>
  );
}

const PAGE_SIZE = 30;

export default function ProfilePage() {
  const { username } = useParams<{ username: string }>();
  const { user } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [activity, setActivity] = useState<FeedItem[] | null>(null);
  const [lists, setLists] = useState<ListSummary[]>([]);
  const [notFound, setNotFound] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  // Re-fetch whenever the username changes or the viewer's auth state settles
  // (so is_following / is_self reflect the signed-in user).
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (!username) return;
    let active = true;
    // Clear stale data so the new profile loads from a blank slate.
    setProfile(null);
    setActivity(null);
    setNotFound(false);
    setHasMore(true);
    api
      .profile(username)
      .then((p) => active && setProfile(p))
      .catch((e) => {
        if (!active) return;
        if (e instanceof ApiError && e.status === 404) setNotFound(true);
      });
    api
      .userActivity(username, PAGE_SIZE, 0)
      .then((a) => {
        if (!active) return;
        setActivity(a);
        setHasMore(a.length === PAGE_SIZE);
      })
      .catch(() => active && setActivity([]));
    api
      .userLists(username)
      .then((l) => active && setLists(l))
      .catch(() => active && setLists([]));
    return () => {
      active = false;
    };
  }, [username, user]);
  /* eslint-enable react-hooks/set-state-in-effect */

  async function loadMore() {
    if (!activity || loadingMore) return;
    setLoadingMore(true);
    try {
      const page = await api.userActivity(username, PAGE_SIZE, activity.length);
      setActivity([...activity, ...page]);
      setHasMore(page.length === PAGE_SIZE);
    } finally {
      setLoadingMore(false);
    }
  }

  if (notFound) {
    return (
      <div>
        <h1 className="text-2xl font-bold">User not found</h1>
        <p className="mt-2 text-white/50">
          No one here goes by “{username}.”{" "}
          <Link href="/" className="text-orange-400 hover:underline">
            Go home
          </Link>
        </p>
      </div>
    );
  }

  if (!profile) return <p className="text-white/50">Loading…</p>;

  const initial = (profile.display_name ?? profile.username)
    .charAt(0)
    .toUpperCase();

  return (
    <div>
      <div className="flex items-start gap-5">
        {profile.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={profile.avatar_url}
            alt={profile.username}
            className="h-20 w-20 rounded-full object-cover"
          />
        ) : (
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-orange-500/20 text-2xl font-bold text-orange-400">
            {initial}
          </div>
        )}
        <div className="flex-1">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold">
                {profile.display_name ?? profile.username}
              </h1>
              <p className="text-sm text-white/40">@{profile.username}</p>
            </div>
            {profile.is_self ? (
              <div className="flex shrink-0 gap-2">
                <Link
                  href="/stats"
                  className="rounded-md border border-white/15 px-4 py-1.5 text-sm text-white/80 hover:border-white/40 hover:text-white"
                >
                  Stats
                </Link>
                <Link
                  href="/settings"
                  className="rounded-md border border-white/15 px-4 py-1.5 text-sm text-white/80 hover:border-white/40 hover:text-white"
                >
                  Edit profile
                </Link>
              </div>
            ) : user ? (
              <FollowButton
                username={profile.username}
                initialFollowing={profile.is_following}
              />
            ) : (
              <Link
                href="/login"
                className="rounded-md bg-orange-500 px-4 py-1.5 text-sm font-medium text-black hover:bg-orange-400"
              >
                Follow
              </Link>
            )}
          </div>
          {profile.bio && (
            <p className="mt-2 max-w-prose text-sm text-white/70">{profile.bio}</p>
          )}
        </div>
      </div>

      <div className="mt-6 flex gap-8 border-y border-white/10 py-4">
        <Stat label="Films" value={profile.stats.films_logged} />
        <Stat label="Reviews" value={profile.stats.reviews} />
        <Link href={`/u/${profile.username}/followers`} className="hover:opacity-80">
          <Stat label="Followers" value={profile.stats.followers} />
        </Link>
        <Link href={`/u/${profile.username}/following`} className="hover:opacity-80">
          <Stat label="Following" value={profile.stats.following} />
        </Link>
      </div>

      {lists.length > 0 && (
        <>
          <h2 className="mb-3 mt-8 text-lg font-semibold">Lists</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {lists.map((l) => (
              <ListCard key={l.id} list={l} />
            ))}
          </div>
        </>
      )}

      <h2 className="mb-3 mt-8 text-lg font-semibold">Recent activity</h2>
      {!activity && <p className="text-white/50">Loading…</p>}
      {activity && activity.length === 0 && (
        <p className="text-white/50">No activity yet.</p>
      )}
      {activity && activity.length > 0 && (
        <div className="space-y-2">
          {activity.map((item) => (
            <ActivityItem key={item.id} item={item} />
          ))}
        </div>
      )}
      {activity && activity.length > 0 && hasMore && (
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
