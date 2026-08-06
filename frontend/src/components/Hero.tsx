/** Homepage hero: project title and a short explanation. */
export function Hero() {
  return (
    <section className="relative overflow-hidden rounded-2xl border border-border bg-surface px-6 py-14 sm:px-10 sm:py-20">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-accent/10 blur-3xl"
      />
      <div className="relative max-w-2xl">
        <span className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-3 py-1 text-xs font-medium text-muted">
          <span className="h-1.5 w-1.5 rounded-full bg-accent" />
          Europe&apos;s top five leagues
        </span>
        <h1 className="mt-4 text-4xl font-bold tracking-tight sm:text-5xl">
          Football Intelligence Platform
        </h1>
        <p className="mt-4 text-base leading-relaxed text-muted sm:text-lg">
          Explore standings, team statistics, and recent results across Europe&apos;s
          major leagues. Clean, fast, and data-driven — every number is served
          live from the platform&apos;s own API.
        </p>
        <div className="mt-6">
          <a
            href="#leagues"
            className="inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-accent-foreground transition hover:opacity-90"
          >
            Browse leagues
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-4 w-4"
              aria-hidden="true"
            >
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </a>
        </div>
      </div>
    </section>
  );
}
