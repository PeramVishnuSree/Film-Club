"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ActivityItem from "@/components/ActivityItem";
import FollowButton from "@/components/FollowButton";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { FeedItem, Profile } from "@/lib/types";

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <div className="text-lg font-bold">{value}</div>
      <div className="text-xs uppercase tracking-wide text-white/40">{label}</div>
    </div>
  );
}

export default function ProfilePage() {
  const { username } = useParams<{ username: string }>();
  const { user } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [activity, setActivity] = useState<FeedItem[] | null>(null);
  const [notFound, setNotFound] = useState(false);

  // Re-fetch whenever the username changes or the viewer's auth state settles
  // (so is_following / is_self reflect the signed-in user).
  useEffect(() => {
    if (!username) return;
    let active = true;
    setProfile(null);
    setActivity(null);
    setNotFound(false);
    api
      .profile(username)
      .then((p) => active && setProfile(p))
      .catch((e) => {
        if (!active) return;
        if (e instanceof ApiError && e.status === 404) setNotFound(true);
      });
    api
      .userActivity(username)
      .then((a) => active && setActivity(a))
      .catch(() => active && setActivity([]));
    return () => {
      active = false;
    };
  }, [username, user]);

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
              <span className="rounded-md border border-white/15 px-3 py-1.5 text-sm text-white/50">
                This is you
              </span>
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
    </div>
  );
}
