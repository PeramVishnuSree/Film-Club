import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy — Film Club",
  description: "How this Film Club instance handles your information.",
};

export default function PrivacyPage() {
  return (
    <article className="prose prose-invert max-w-2xl">
      <h1 className="text-2xl font-bold">Privacy Policy</h1>
      <p className="mt-2 text-sm text-white/50">
        Film Club is self-hostable software. The operator of this instance is
        responsible for the authoritative policy; this page summarizes the
        defaults shipped with the software.
      </p>

      <h2 className="mt-8 text-lg font-semibold">Information we collect</h2>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-white/70">
        <li>
          <strong>Account information</strong> you provide: username, email,
          password (stored only as a salted hash), and optional profile details.
        </li>
        <li>
          <strong>Content you create:</strong> diary entries, ratings, reviews,
          lists, watchlist items, follows, and likes.
        </li>
        <li>
          <strong>Imported data:</strong> entries from a Letterboxd CSV, if you
          choose to import one.
        </li>
        <li>
          <strong>Technical data:</strong> standard server logs (IP address,
          request time, user agent).
        </li>
      </ul>
      <p className="mt-2 text-sm text-white/70">
        We do not serve ads, and we do not sell your personal information.
      </p>

      <h2 className="mt-8 text-lg font-semibold">Third-party services</h2>
      <p className="mt-2 text-sm text-white/70">
        Film metadata and images come from{" "}
        <a
          href="https://www.themoviedb.org/"
          target="_blank"
          rel="noreferrer"
          className="text-orange-400 hover:underline"
        >
          The Movie Database (TMDB)
        </a>
        . If email is configured, transactional messages (verification, password
        reset) are sent through an SMTP provider. Hosting infrastructure may
        process technical data to deliver the service.
      </p>

      <h2 className="mt-8 text-lg font-semibold">Cookies and storage</h2>
      <p className="mt-2 text-sm text-white/70">
        Authentication uses a token stored in your browser&apos;s local storage.
        We do not use third-party tracking or advertising cookies.
      </p>

      <h2 className="mt-8 text-lg font-semibold">Your choices</h2>
      <p className="mt-2 text-sm text-white/70">
        You can edit most profile fields in{" "}
        <Link href="/settings" className="text-orange-400 hover:underline">
          Settings
        </Link>
        , verify your email, and request account deletion from the operator.
      </p>

      <p className="mt-8 text-xs text-white/40">
        Operators: the full template lives in <code>PRIVACY.md</code> in the
        repository.
      </p>
    </article>
  );
}
