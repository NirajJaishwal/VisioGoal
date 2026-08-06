import { z } from "zod";

/**
 * Zod schemas mirroring the FastAPI response models. Parsing responses through
 * these gives us runtime validation *and* the single source of truth for the
 * TypeScript types (via `z.infer`).
 */

export const teamRefSchema = z.object({
  id: z.number(),
  name: z.string(),
  short_name: z.string().nullable().optional(),
  crest_url: z.string().nullable().optional(),
});
export type TeamRef = z.infer<typeof teamRefSchema>;

export const leagueSchema = z.object({
  id: z.number(),
  external_id: z.number(),
  name: z.string(),
  country: z.string(),
  season: z.number(),
});
export type League = z.infer<typeof leagueSchema>;

export const standingSchema = z.object({
  league_id: z.number(),
  season: z.number(),
  position: z.number(),
  team: teamRefSchema,
  played: z.number(),
  won: z.number(),
  drawn: z.number(),
  lost: z.number(),
  goals_for: z.number(),
  goals_against: z.number(),
  goal_difference: z.number(),
  points: z.number(),
});
export type Standing = z.infer<typeof standingSchema>;

export const matchSchema = z.object({
  id: z.number(),
  external_id: z.number(),
  league_id: z.number(),
  season: z.number().nullable(),
  matchday: z.number().nullable(),
  status: z.string(),
  kickoff_datetime: z.string().nullable(),
  home_team: teamRefSchema,
  away_team: teamRefSchema,
  home_score: z.number().nullable(),
  away_score: z.number().nullable(),
});
export type Match = z.infer<typeof matchSchema>;

/** Generic paginated envelope: `{ items, total, limit, offset }`. */
export function pageSchema<T extends z.ZodTypeAny>(item: T) {
  return z.object({
    items: z.array(item),
    total: z.number(),
    limit: z.number(),
    offset: z.number(),
  });
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
