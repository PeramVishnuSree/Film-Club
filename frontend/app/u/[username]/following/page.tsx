"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import UserCardRow from "@/components/UserCardRow";
import { api } from "@/lib/api";
import type { UserCard } from "@/lib/types";

export default function FollowingPage() {
  const { username } = useParams<{ username: string }>();
  const [users, setUsers] = useState<UserCard[] | null>(null);

  useEffect(() => {
    if (!username) return;
    let active = true;
    api
      .following(username)
      .then((u) => active && setUsers(u))
      .catch(() => active && setUsers([]));
    return () => {
      active = false;
    };
  }, [username]);

  return (
    <div>
      <Link
        href={`/u/${username}`}
        className="text-sm text-white/50 hover:text-white"
      >
        ← @{username}
      </Link>
      <h1 className="mb-4 mt-2 text-2xl font-bold">Following</h1>
      {!users && <p className="text-white/50">Loading…</p>}
      {users && users.length === 0 && (
        <p className="text-white/50">Not following anyone yet.</p>
      )}
      {users && users.length > 0 && (
        <div className="space-y-2">
          {users.map((u) => (
            <UserCardRow key={u.id} user={u} />
          ))}
        </div>
      )}
    </div>
  );
}
