"use client";

import { MatchRow } from "@/components/MatchRow";
import { ErrorRetry } from "@/components/ui/ErrorRetry";
import { Skeleton } from "@/components/ui/Skeleton";
import { useRecentMatches } from "@/lib/queries";

/** Latest finished matches across all leagues. */
export function RecentMatches() {
  const { data, isLoading, isError, refetch } = useRecentMatches(8);

  return (
    <section>
      <div className="mb-4 flex items-end justify-between">
        <h2 className="text-xl font-semibold">Recent Matches</h2>
        <p className="text-sm text-muted">Latest results</p>
      </div>

      {isLoading && (
        <ul className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <li
              key={i}
              className="flex items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3"
            >
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-4 w-32" />
              </div>
              <Skeleton className="h-10 w-10" />
            </li>
          ))}
        </ul>
      )}

      {isError && (
        <ErrorRetry
          message="We couldn't load recent matches."
          onRetry={() => refetch()}
        />
      )}

      {data &&
        (data.length === 0 ? (
          <p className="rounded-xl border border-border bg-surface p-6 text-center text-sm text-muted">
            No finished matches yet.
          </p>
        ) : (
          <ul className="space-y-3">
            {data.map((match) => (
              <MatchRow key={match.id} match={match} />
            ))}
          </ul>
        ))}
    </section>
  );
}
