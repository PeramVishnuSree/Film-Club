"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";

type Status = "working" | "ok" | "error";

function VerifyEmail() {
  const params = useSearchParams();
  const token = params.get("token") ?? "";
  const [status, setStatus] = useState<Status>("working");
  const [message, setMessage] = useState("Verifying your email…");
  const ran = useRef(false);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    // Guard against the effect firing twice in React strict mode.
    if (ran.current) return;
    ran.current = true;

    if (!token) {
      setStatus("error");
      setMessage("This verification link is missing its token.");
      return;
    }
    api
      .confirmEmailVerification(token)
      .then((res) => {
        setStatus("ok");
        setMessage(res.detail);
      })
      .catch((err) => {
        setStatus("error");
        setMessage(
          err instanceof ApiError ? err.message : "Could not verify your email.",
        );
      });
  }, [token]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const tone =
    status === "ok"
      ? "border-orange-400/30 bg-orange-400/10 text-orange-200"
      : status === "error"
        ? "border-red-400/30 bg-red-400/10 text-red-300"
        : "border-white/15 bg-white/5 text-white/70";

  return (
    <div className={`rounded-md border p-4 text-sm ${tone}`}>
      <p>{message}</p>
      {status !== "working" && (
        <Link href="/" className="mt-3 inline-block text-orange-400 hover:underline">
          Go home
        </Link>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-6 text-2xl font-bold">Email verification</h1>
      <Suspense fallback={<p className="text-white/50">Loading…</p>}>
        <VerifyEmail />
      </Suspense>
    </div>
  );
}
