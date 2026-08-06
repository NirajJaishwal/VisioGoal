import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About · Football Intelligence Platform",
};

const STACK = [
  "Next.js (App Router)",
  "TypeScript",
  "TailwindCSS",
  "TanStack Query",
  "Recharts",
  "FastAPI + PostgreSQL",
];

/** Static project description. No football data is hardcoded here. */
export default function AboutPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">About</h1>
        <p className="mt-3 leading-relaxed text-muted">
          The Football Intelligence Platform is a football analytics dashboard for
          Europe&apos;s top five leagues. It presents league standings, basic team
          statistics, and recent results in a clean, responsive interface.
        </p>
      </div>

      <div className="rounded-xl border border-border bg-surface p-5">
        <h2 className="font-semibold">How it works</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          Match and standings data are ingested from Football-Data.org into a
          PostgreSQL database and served through a versioned FastAPI REST API. This
          dashboard is a read-only client of that API — it performs no calculations
          of its own and never talks to the database directly.
        </p>
      </div>

      <div className="rounded-xl border border-border bg-surface p-5">
        <h2 className="font-semibold">Built with</h2>
        <ul className="mt-3 flex flex-wrap gap-2">
          {STACK.map((item) => (
            <li
              key={item}
              className="rounded-md border border-border bg-background px-2.5 py-1 text-xs font-medium text-muted"
            >
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
