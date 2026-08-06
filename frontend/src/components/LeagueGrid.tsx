"use client";

import { LeagueCard } from "@/components/LeagueCard";
import { ErrorRetry } from "@/components/ui/ErrorRetry";
import { Skeleton } from "@/components/ui/Skeleton";
import { useLeagues } from "@/lib/queries";

/** Section listing all leagues as cards, with loading and error states. */
export function LeagueGrid() {
  const { data, isLoading, isError, refetch } = useLeagues();

  return (
    <section id="leagues" className="scroll-mt-20">
      <div className="mb-4 flex items-end justify-between">
        <h2 className="text-xl font-semibold">Leagues</h2>
        <p className="text-sm text-muted">Select a league to view its table</p>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="rounded-xl border border-border bg-surface p-5"
            >
              <Skeleton className="h-5 w-32" />
              <Skeleton className="mt-2 h-4 w-20" />
              <Skeleton className="mt-6 h-4 w-28" />
            </div>
          ))}
        </div>
      )}

      {isError && (
        <ErrorRetry
          message="We couldn't load the leagues."
          onRetry={() => refetch()}
        />
      )}

      {data && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.map((league) => (
            <LeagueCard key={league.id} league={league} />
          ))}
        </div>
      )}
    </section>
  );
}
