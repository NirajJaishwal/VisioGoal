import { z } from "zod";

import {
  leagueSchema,
  matchSchema,
  pageSchema,
  standingSchema,
  type League,
  type Match,
  type Standing,
} from "@/types/api";

/**
 * Typed API client. The single place that talks to the REST API — every screen
 * goes through these functions, so there is no duplicated fetch code.
 *
 * Base URL is a *relative* path by default so requests are same-origin and get
 * proxied to the backend by Next rewrites (avoids CORS). An override is honored
 * only if it is itself relative, to keep that guarantee.
 */
const configuredBase = process.env.NEXT_PUBLIC_API_BASE_URL;
const BASE =
  configuredBase && configuredBase.startsWith("/") ? configuredBase : "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { Accept: "application/json" },
    });
  } catch {
    throw new ApiError("Could not reach the server. Check your connection.", 0);
  }

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { error?: { message?: string } };
      if (body?.error?.message) message = body.error.message;
    } catch {
      /* non-JSON error body — keep the default message */
    }
    throw new ApiError(message, res.status);
  }

  return schema.parse(await res.json());
}

export function getLeagues(): Promise<League[]> {
  return request("/leagues", z.array(leagueSchema));
}

export function getLeague(leagueId: number): Promise<League> {
  return request(`/leagues/${leagueId}`, leagueSchema);
}

export function getStandings(
  leagueId: number,
  season?: number,
): Promise<Standing[]> {
  const query = season != null ? `?season=${season}` : "";
  return request(`/leagues/${leagueId}/standings${query}`, z.array(standingSchema));
}

/**
 * Latest finished matches. The API orders matches by kick-off ascending and has
 * no sort param, so we read the total, request the final page, and reverse it to
 * present newest-first — using only the public API, no server logic duplicated.
 */
export async function getRecentMatches(limit = 8): Promise<Match[]> {
  const matchPage = pageSchema(matchSchema);
  const head = await request(
    `/matches?status=FINISHED&limit=1`,
    matchPage,
  );
  const offset = Math.max(0, head.total - limit);
  const page = await request(
    `/matches?status=FINISHED&limit=${limit}&offset=${offset}`,
    matchPage,
  );
  return [...page.items].reverse();
}
