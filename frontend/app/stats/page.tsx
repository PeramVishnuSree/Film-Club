"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, posterUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Stats } from "@/lib/types";

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
      <p className="text-2xl font-bold text-orange-400">{value}</p>
      <p className="mt-0.5 text-xs uppercase tracking-wide text-white/50">
        {label}
      </p>
    </div>
  );
}

export default function StatsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [year, setYear] = useState<number | undefined>(undefined);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (user) api.stats(year).then(setStats).catch(() => setStats(null));
  }, [user, year]);

  if (loading || !user) return <p className="text-white/50">Loading…</p>;
  if (!stats) return <p className="text-white/50">Loading…</p>;

  const { lifetime, year: y, available_years } = stats;
  const maxMonth = Math.max(1, ...y.by_month.map((m) => m.count));
  const maxBucket = Math.max(1, ...lifetime.rating_distribution.map((b) => b.count));

  return (
    <div className="space-y-10">
      <div>
        <h1 className="mb-1 text-2xl font-bold">Your stats</h1>
        <p className="text-sm text-white/50">A look back at what you’ve watched.</p>
      </div>

      {/* Lifetime totals */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">All time</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <StatCard label="Films" value={lifetime.films_logged} />
          <StatCard label="Entries" value={lifetime.entries} />
          <StatCard label="Ratings" value={lifetime.ratings} />
          <StatCard label="Reviews" value={lifetime.reviews} />
          <StatCard label="Lists" value={lifetime.lists} />
          <StatCard
            label="Avg rating"
            value={lifetime.average_rating != null ? lifetime.average_rating.toFixed(2) : "—"}
          />
        </div>

        {/* Rating distribution */}
        <div className="mt-6 rounded-lg border border-white/10 bg-white/[0.03] p-4">
          <p className="mb-3 text-sm font-medium text-white/70">
            Rating distribution
          </p>
          <div className="flex items-end gap-1.5" style={{ height: 120 }}>
            {lifetime.rating_distribution.map((b) => (
              <div key={b.value} className="flex flex-1 flex-col items-center gap-1">
                <div
                  className="w-full rounded-t bg-orange-500/70"
                  style={{ height: `${(b.count / maxBucket) * 90}px` }}
                  title={`${b.count} at ${b.value}★`}
                />
                <span className="text-[10px] text-white/40">{b.value}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Year in review */}
      <section>
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">{y.year} in review</h2>
          {available_years.length > 0 && (
            <select
              value={year ?? y.year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="rounded-md border border-white/15 bg-white/5 px-2 py-1 text-sm outline-none focus:border-orange-400"
            >
              {available_years.map((yr) => (
                <option key={yr} value={yr} className="bg-black">
                  {yr}
                </option>
              ))}
            </select>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <StatCard label="Films watched" value={y.entries} />
          <StatCard label="Distinct films" value={y.distinct_films} />
          <StatCard label="Hours" value={y.hours} />
        </div>

        {/* Watches by month */}
        <div className="mt-6 rounded-lg border border-white/10 bg-white/[0.03] p-4">
          <p className="mb-3 text-sm font-medium text-white/70">By month</p>
          <div className="flex items-end gap-1.5" style={{ height: 120 }}>
            {y.by_month.map((m) => (
              <div key={m.month} className="flex flex-1 flex-col items-center gap-1">
                <div
                  className="w-full rounded-t bg-orange-500/70"
                  style={{ height: `${(m.count / maxMonth) * 90}px` }}
                  title={`${m.count} in ${MONTHS[m.month - 1]}`}
                />
                <span className="text-[10px] text-white/40">
                  {MONTHS[m.month - 1][0]}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top genres */}
        {y.top_genres.length > 0 && (
          <div className="mt-6">
            <p className="mb-2 text-sm font-medium text-white/70">Top genres</p>
            <div className="flex flex-wrap gap-2">
              {y.top_genres.map((g) => (
                <span
                  key={g.name}
                  className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-sm text-white/80"
                >
                  {g.name} <span className="text-white/40">{g.count}</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Top films */}
        {y.top_films.length > 0 && (
          <div className="mt-6">
            <p className="mb-2 text-sm font-medium text-white/70">
              Highest rated this year
            </p>
            <div className="flex gap-3 overflow-x-auto pb-2">
              {y.top_films.map((f) => (
                <Link
                  key={f.tmdb_id}
                  href={`/film/${f.tmdb_id}`}
                  className="w-24 shrink-0"
                >
                  {f.poster_path ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={posterUrl(f.poster_path, "w154") ?? ""}
                      alt={f.title}
                      className="aspect-[2/3] w-full rounded object-cover"
                    />
                  ) : (
                    <div className="flex aspect-[2/3] w-full items-center justify-center rounded bg-white/10 p-1 text-center text-[10px] text-white/40">
                      {f.title}
                    </div>
                  )}
                  <p className="mt-1 truncate text-xs" title={f.title}>
                    {f.title}
                  </p>
                  {f.rating != null && (
                    <p className="text-[11px] text-orange-400">★ {f.rating}</p>
                  )}
                </Link>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
