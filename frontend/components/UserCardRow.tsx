import Link from "next/link";
import type { UserCard } from "@/lib/types";

export default function UserCardRow({ user }: { user: UserCard }) {
  const initial = (user.display_name ?? user.username).charAt(0).toUpperCase();
  return (
    <Link
      href={`/u/${user.username}`}
      className="flex items-center gap-3 rounded-lg border border-white/10 bg-white/[0.03] p-3 hover:border-white/20"
    >
      {user.avatar_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={user.avatar_url}
          alt={user.username}
          className="h-10 w-10 rounded-full object-cover"
        />
      ) : (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-500/20 text-sm font-bold text-orange-400">
          {initial}
        </div>
      )}
      <div className="min-w-0">
        <div className="truncate font-medium">
          {user.display_name ?? user.username}
        </div>
        <div className="truncate text-xs text-white/40">@{user.username}</div>
      </div>
    </Link>
  );
}
