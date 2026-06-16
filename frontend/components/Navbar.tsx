"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth";

export default function Navbar() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [q, setQ] = useState("");

  function onSearch(e: React.FormEvent) {
    e.preventDefault();
    if (q.trim()) router.push(`/search?q=${encodeURIComponent(q.trim())}`);
  }

  return (
    <header className="border-b border-white/10 bg-black/30 backdrop-blur sticky top-0 z-10">
      <nav className="mx-auto flex max-w-5xl items-center gap-4 px-4 py-3">
        <Link href="/" className="text-lg font-bold tracking-tight">
          Film<span className="text-orange-400">Club</span>
        </Link>
        <Link href="/trending" className="text-sm text-white/70 hover:text-white">
          Trending
        </Link>
        <Link href="/top500" className="text-sm text-white/70 hover:text-white">
          Top 500
        </Link>
        {user && (
          <>
            <Link href="/feed" className="text-sm text-white/70 hover:text-white">
              Feed
            </Link>
            <Link href="/watchlist" className="text-sm text-white/70 hover:text-white">
              Watchlist
            </Link>
            <Link href="/diary" className="text-sm text-white/70 hover:text-white">
              Diary
            </Link>
          </>
        )}
        <form onSubmit={onSearch} className="ml-auto">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search films…"
            className="w-40 rounded-md border border-white/15 bg-white/5 px-3 py-1.5 text-sm outline-none focus:border-orange-400 sm:w-56"
          />
        </form>
        {user ? (
          <div className="flex items-center gap-3">
            <Link
              href={`/u/${user.username}`}
              className="text-sm text-white/70 hover:text-white"
            >
              {user.display_name ?? user.username}
            </Link>
            <button
              onClick={logout}
              className="text-sm text-white/70 hover:text-white"
            >
              Log out
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm text-white/70 hover:text-white">
              Log in
            </Link>
            <Link
              href="/signup"
              className="rounded-md bg-orange-500 px-3 py-1.5 text-sm font-medium text-black hover:bg-orange-400"
            >
              Sign up
            </Link>
          </div>
        )}
      </nav>
    </header>
  );
}
