"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function FollowButton({
  username,
  initialFollowing,
  onChange,
}: {
  username: string;
  initialFollowing: boolean;
  onChange?: (following: boolean) => void;
}) {
  const [following, setFollowing] = useState(initialFollowing);
  const [busy, setBusy] = useState(false);

  async function toggle() {
    if (busy) return;
    setBusy(true);
    const next = !following;
    setFollowing(next); // optimistic
    try {
      if (next) await api.follow(username);
      else await api.unfollow(username);
      onChange?.(next);
    } catch {
      setFollowing(!next); // revert on failure
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      onClick={toggle}
      disabled={busy}
      className={
        following
          ? "rounded-md border border-white/20 px-4 py-1.5 text-sm font-medium text-white/80 hover:border-white/40 hover:text-white disabled:opacity-60"
          : "rounded-md bg-orange-500 px-4 py-1.5 text-sm font-medium text-black hover:bg-orange-400 disabled:opacity-60"
      }
    >
      {following ? "Following" : "Follow"}
    </button>
  );
}
