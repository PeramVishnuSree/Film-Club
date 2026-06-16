"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ImportResult } from "@/lib/types";

export default function ImportPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  async function onFile(file: File) {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await api.importLetterboxd(file));
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Import failed. Please try again.",
      );
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  if (loading || !user) return <p className="text-white/50">Loading…</p>;

  return (
    <div className="max-w-prose">
      <h1 className="mb-1 text-2xl font-bold">Import from Letterboxd</h1>
      <p className="mb-6 text-sm text-white/60">
        Export your data from Letterboxd (Settings → Import &amp; Export → Export
        your data), unzip it, and upload one file at a time:{" "}
        <code className="rounded bg-white/10 px-1">diary.csv</code>,{" "}
        <code className="rounded bg-white/10 px-1">ratings.csv</code>, or{" "}
        <code className="rounded bg-white/10 px-1">watchlist.csv</code>. We’ll
        match each film to TMDB automatically.
      </p>

      <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-white/20 bg-white/[0.03] p-8 text-center hover:border-orange-400/60">
        <span className="text-sm text-white/70">
          {busy ? "Importing…" : "Choose a CSV file"}
        </span>
        <span className="text-xs text-white/40">
          The file type is detected automatically.
        </span>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          disabled={busy}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onFile(f);
          }}
          className="hidden"
        />
      </label>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      {result && (
        <div className="mt-6 rounded-lg border border-white/10 bg-white/[0.03] p-4">
          <p className="mb-2 text-sm font-medium">
            Imported your{" "}
            <span className="text-orange-400">{result.kind}</span> file.
          </p>
          <ul className="space-y-1 text-sm text-white/70">
            <li>{result.rows} rows read</li>
            <li className="text-green-400">{result.imported} imported</li>
            <li>{result.skipped} skipped (already present)</li>
            <li>{result.unmatched.length} unmatched</li>
          </ul>
          {result.unmatched.length > 0 && (
            <details className="mt-3">
              <summary className="cursor-pointer text-sm text-white/60 hover:text-white">
                Show unmatched titles
              </summary>
              <ul className="mt-2 space-y-0.5 text-xs text-white/50">
                {result.unmatched.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
