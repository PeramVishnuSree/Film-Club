import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 bg-black/30">
      <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 py-6 text-sm text-white/50 sm:flex-row sm:items-center sm:justify-between">
        <p>
          <span className="font-semibold text-white/70">
            Film<span className="text-orange-400">Club</span>
          </span>{" "}
          — an open-source, ad-free film log.
        </p>
        <nav className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <Link href="/privacy" className="hover:text-white">
            Privacy
          </Link>
          <Link href="/terms" className="hover:text-white">
            Terms
          </Link>
          <a
            href="https://github.com/"
            target="_blank"
            rel="noreferrer"
            className="hover:text-white"
          >
            Source
          </a>
          <a
            href="https://www.themoviedb.org/"
            target="_blank"
            rel="noreferrer"
            className="hover:text-white"
          >
            Powered by TMDB
          </a>
        </nav>
      </div>
      <div className="mx-auto max-w-5xl px-4 pb-6 text-xs text-white/30">
        This product uses the TMDB API but is not endorsed or certified by TMDB.
      </div>
    </footer>
  );
}
