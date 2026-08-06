"use client";

import Link from "next/link";

import { GoalsScatterChart } from "@/components/charts/GoalsScatterChart";
import { PointsBarChart } from "@/components/charts/PointsBarChart";
import { StandingsTable } from "@/components/StandingsTable";
import { ErrorRetry } from "@/components/ui/ErrorRetry";
import { Skeleton } from "@/components/ui/Skeleton";
import { useLeague, useStandings } from "@/lib/queries";
import { formatSeason } from "@/lib/utils";

/** League standings page: header, sortable table, and charts. */
export function LeaguePageClient({ leagueId }: { leagueId: number }) {
  const league = useLeague(leagueId);
  const season = league.data?.season;
  const standings = useStandings(leagueId, season);

  if (!Number.isFinite(leagueId)) {
    return <ErrorRetry title="Invalid league" message="That league id is not valid." />;
  }

  if (league.isError) {
    return (
      <ErrorRetry
        title="League not found"
        message="We couldn't load this league. It may not exist."
        onRetry={() => league.refetch()}
      />
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/"
          className="inline-flex items-center gap-1 text-sm text-muted transition hover:text-foreground"
        >
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
            <path d="M19 12H5M11 18l-6-6 6-6" />
          </svg>
          All leagues
        </Link>

        {league.isLoading ? (
          <div className="mt-3 space-y-2">
            <Skeleton className="h-8 w-56" />
            <Skeleton className="h-4 w-32" />
          </div>
        ) : (
          league.data && (
            <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1">
              <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
                {league.data.name}
              </h1>
              <span className="rounded-md bg-accent/10 px-2 py-1 text-xs font-medium text-accent">
                {formatSeason(league.data.season)}
              </span>
              <span className="w-full text-sm text-muted sm:w-auto">
                {league.data.country}
              </span>
            </div>
          )
        )}
      </div>

      {/* Standings */}
      {standings.isError ? (
        <ErrorRetry
          message="We couldn't load the standings."
          onRetry={() => standings.refetch()}
        />
      ) : standings.isLoading || league.isLoading ? (
        <TableSkeleton />
      ) : standings.data && standings.data.length > 0 ? (
        <>
          <StandingsTable standings={standings.data} />
          <div className="grid gap-6 lg:grid-cols-2">
            <PointsBarChart standings={standings.data} />
            <GoalsScatterChart standings={standings.data} />
          </div>
        </>
      ) : (
        <p className="rounded-xl border border-border bg-surface p-6 text-center text-sm text-muted">
          No standings available for this season yet.
        </p>
      )}
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-3 rounded-xl border border-border bg-surface p-4">
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="h-5 w-5" />
          <Skeleton className="h-5 flex-1" />
          <Skeleton className="h-5 w-10" />
        </div>
      ))}
    </div>
  );
}
