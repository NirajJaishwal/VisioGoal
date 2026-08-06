import { Hero } from "@/components/Hero";
import { LeagueGrid } from "@/components/LeagueGrid";
import { RecentMatches } from "@/components/RecentMatches";

/** Dashboard homepage. */
export default function Home() {
  return (
    <div className="space-y-10">
      <Hero />
      <LeagueGrid />
      <RecentMatches />
    </div>
  );
}
