import Link from "next/link";

import { formatSeason } from "@/lib/utils";
import type { League } from "@/types/api";

/** A single league tile linking to its standings page. */
export function LeagueCard({ league }: { league: League }) {
  return (
    <Link
      href={`/team/${league.id}`}
      className="group flex flex-col justify-between rounded-xl border border-border bg-surface p-5 transition hover:border-accent/60 hover:shadow-sm"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold leading-tight">{league.name}</h3>
          <p className="mt-1 text-sm text-muted">{league.country}</p>
        </div>
        <span className="rounded-md bg-accent/10 px-2 py-1 text-xs font-medium text-accent">
          {formatSeason(league.season)}
        </span>
      </div>
      <div className="mt-6 flex items-center gap-1 text-sm font-medium text-muted transition group-hover:text-accent">
        View standings
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-4 w-4 transition group-hover:translate-x-0.5"
          aria-hidden="true"
        >
          <path d="M5 12h14M13 6l6 6-6 6" />
        </svg>
      </div>
    </Link>
  );
}
