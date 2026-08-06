import { LeaguePageClient } from "@/components/LeaguePageClient";

/**
 * League standings route. The dynamic segment is a league id; the page reads it
 * and delegates to a client component that fetches and renders the table/charts.
 */
export default async function TeamStandingsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <LeaguePageClient leagueId={Number(id)} />;
}
