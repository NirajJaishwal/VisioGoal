import { TeamCrest } from "@/components/ui/TeamCrest";
import { cn, formatMatchDate } from "@/lib/utils";
import type { Match } from "@/types/api";

/** One finished match: home vs away with the final score. */
export function MatchRow({ match }: { match: Match }) {
  const home = match.home_score ?? 0;
  const away = match.away_score ?? 0;
  const homeWin = home > away;
  const awayWin = away > home;

  return (
    <li className="flex items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3">
      <div className="min-w-0 flex-1">
        <TeamSide name={match.home_team.name} crest={match.home_team.crest_url} highlight={homeWin} align="left" />
        <TeamSide name={match.away_team.name} crest={match.away_team.crest_url} highlight={awayWin} align="left" />
      </div>

      <div className="flex flex-col items-center rounded-lg bg-background px-3 py-1 text-center font-semibold tabular-nums">
        <span className={cn(!homeWin && "text-muted")}>{home}</span>
        <span className={cn(!awayWin && "text-muted")}>{away}</span>
      </div>

      <div className="hidden w-24 shrink-0 text-right text-xs text-muted sm:block">
        {match.matchday != null && <div>MD {match.matchday}</div>}
        <div>{formatMatchDate(match.kickoff_datetime)}</div>
      </div>
    </li>
  );
}

function TeamSide({
  name,
  crest,
  highlight,
  align,
}: {
  name: string;
  crest?: string | null;
  highlight: boolean;
  align: "left" | "right";
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 py-0.5",
        align === "right" && "flex-row-reverse text-right",
      )}
    >
      <TeamCrest name={name} src={crest} size={20} />
      <span
        className={cn(
          "truncate text-sm",
          highlight ? "font-semibold text-foreground" : "text-muted",
        )}
      >
        {name}
      </span>
    </div>
  );
}
