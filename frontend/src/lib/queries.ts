import { useQuery } from "@tanstack/react-query";

import {
  getLeague,
  getLeagues,
  getRecentMatches,
  getStandings,
} from "@/lib/api";

/** Centralized query keys so caches are consistent and easy to invalidate. */
export const queryKeys = {
  leagues: ["leagues"] as const,
  league: (id: number) => ["league", id] as const,
  standings: (id: number, season?: number) =>
    ["standings", id, season ?? null] as const,
  recentMatches: (limit: number) => ["recent-matches", limit] as const,
};

export function useLeagues() {
  return useQuery({ queryKey: queryKeys.leagues, queryFn: getLeagues });
}

export function useLeague(id: number) {
  return useQuery({
    queryKey: queryKeys.league(id),
    queryFn: () => getLeague(id),
    enabled: Number.isFinite(id),
  });
}

export function useStandings(id: number, season?: number) {
  return useQuery({
    queryKey: queryKeys.standings(id, season),
    queryFn: () => getStandings(id, season),
    // Wait until we know which season to request.
    enabled: Number.isFinite(id) && season != null,
  });
}

export function useRecentMatches(limit = 8) {
  return useQuery({
    queryKey: queryKeys.recentMatches(limit),
    queryFn: () => getRecentMatches(limit),
  });
}
