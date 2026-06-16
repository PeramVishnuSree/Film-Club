import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service — Film Club",
  description: "The terms that govern use of this Film Club instance.",
};

export default function TermsPage() {
  return (
    <article className="prose prose-invert max-w-2xl">
      <h1 className="text-2xl font-bold">Terms of Service</h1>
      <p className="mt-2 text-sm text-white/50">
        Film Club is self-hostable software. The operator of this instance is
        responsible for the authoritative terms; this page summarizes the
        defaults shipped with the software.
      </p>

      <h2 className="mt-8 text-lg font-semibold">Accounts</h2>
      <p className="mt-2 text-sm text-white/70">
        Provide an accurate email and keep your password secure. You are
        responsible for activity under your account.
      </p>

      <h2 className="mt-8 text-lg font-semibold">Acceptable use</h2>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-white/70">
        <li>Don&apos;t post unlawful, infringing, harassing, or abusive content.</li>
        <li>Don&apos;t disrupt, overload, or attempt unauthorized access.</li>
        <li>Don&apos;t scrape or misuse data beyond normal personal use.</li>
        <li>Don&apos;t use the service to violate the rights of others.</li>
      </ul>

      <h2 className="mt-8 text-lg font-semibold">Your content</h2>
      <p className="mt-2 text-sm text-white/70">
        You keep ownership of the content you create. By posting public content
        you grant the operator a license to host and display it as part of
        running the service.
      </p>

      <h2 className="mt-8 text-lg font-semibold">Film data and TMDB</h2>
      <p className="mt-2 text-sm text-white/70">
        Film metadata and images are provided by{" "}
        <a
          href="https://www.themoviedb.org/"
          target="_blank"
          rel="noreferrer"
          className="text-orange-400 hover:underline"
        >
          TMDB
        </a>
        . This product uses the TMDB API but is not endorsed or certified by
        TMDB.
      </p>

      <h2 className="mt-8 text-lg font-semibold">Availability and liability</h2>
      <p className="mt-2 text-sm text-white/70">
        The service is provided &quot;as is&quot; and &quot;as available,&quot;
        without warranties. To the maximum extent permitted by law, the operator
        is not liable for indirect or consequential damages arising from your
        use of the service.
      </p>

      <h2 className="mt-8 text-lg font-semibold">Software license</h2>
      <p className="mt-2 text-sm text-white/70">
        The Film Club software is licensed under the GNU AGPL-3.0. These terms
        govern use of this hosted instance, not the underlying software license.
      </p>

      <p className="mt-8 text-xs text-white/40">
        Operators: the full template lives in <code>TERMS.md</code> in the
        repository.
      </p>
    </article>
  );
}
