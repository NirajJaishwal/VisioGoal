"use client";

import { useMemo, useState } from "react";

import { TeamCrest } from "@/components/ui/TeamCrest";
import { cn } from "@/lib/utils";
import type { Standing } from "@/types/api";

type SortKey =
  | "position"
  | "club"
  | "played"
  | "won"
  | "drawn"
  | "lost"
  | "goals_for"
  | "goals_against"
  | "goal_difference"
  | "points";

type Column = {
  key: SortKey;
  label: string;
  short: string;
  numeric: boolean;
  /** Hide below this breakpoint to stay readable on small screens. */
  hide?: "sm" | "md";
};

const COLUMNS: Column[] = [
  { key: "position", label: "Position", short: "#", numeric: true },
  { key: "club", label: "Club", short: "Club", numeric: false },
  { key: "played", label: "Played", short: "P", numeric: true, hide: "sm" },
  { key: "won", label: "Wins", short: "W", numeric: true, hide: "sm" },
  { key: "drawn", label: "Draws", short: "D", numeric: true, hide: "sm" },
  { key: "lost", label: "Losses", short: "L", numeric: true, hide: "sm" },
  { key: "goals_for", label: "Goals For", short: "GF", numeric: true, hide: "md" },
  { key: "goals_against", label: "Goals Against", short: "GA", numeric: true, hide: "md" },
  { key: "goal_difference", label: "Goal Difference", short: "GD", numeric: true },
  { key: "points", label: "Points", short: "Pts", numeric: true },
];

const hideClass: Record<NonNullable<Column["hide"]>, string> = {
  sm: "hidden sm:table-cell",
  md: "hidden md:table-cell",
};

function valueFor(row: Standing, key: SortKey): number | string {
  return key === "club" ? row.team.name : row[key];
}

export function StandingsTable({ standings }: { standings: Standing[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("position");
  const [asc, setAsc] = useState(true);

  const sorted = useMemo(() => {
    const rows = [...standings];
    rows.sort((a, b) => {
      const av = valueFor(a, sortKey);
      const bv = valueFor(b, sortKey);
      const cmp =
        typeof av === "string" && typeof bv === "string"
          ? av.localeCompare(bv)
          : Number(av) - Number(bv);
      return asc ? cmp : -cmp;
    });
    return rows;
  }, [standings, sortKey, asc]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setAsc((prev) => !prev);
    } else {
      setSortKey(key);
      // Numeric stats read best high-to-low; position/club low-to-high.
      setAsc(key === "position" || key === "club");
    }
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-border bg-surface">
      <table className="w-full min-w-[520px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-muted">
            {COLUMNS.map((col) => {
              const active = col.key === sortKey;
              return (
                <th
                  key={col.key}
                  scope="col"
                  aria-sort={active ? (asc ? "ascending" : "descending") : "none"}
                  className={cn(
                    "px-3 py-3 font-medium",
                    col.key === "club" ? "text-left" : "text-center",
                    col.hide && hideClass[col.hide],
                  )}
                >
                  <button
                    type="button"
                    onClick={() => toggleSort(col.key)}
                    className={cn(
                      "inline-flex items-center gap-1 transition hover:text-foreground",
                      col.key === "club" ? "" : "justify-center",
                      active && "text-foreground",
                    )}
                    title={`Sort by ${col.label}`}
                  >
                    <span title={col.label}>{col.short}</span>
                    <span className="text-[10px]">
                      {active ? (asc ? "▲" : "▼") : ""}
                    </span>
                  </button>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr
              key={row.team.id}
              className="border-b border-border/60 last:border-0 hover:bg-background/60"
            >
              <td className="px-3 py-2.5 text-center tabular-nums text-muted">
                {row.position}
              </td>
              <td className="px-3 py-2.5">
                <div className="flex items-center gap-2">
                  <TeamCrest name={row.team.name} src={row.team.crest_url} size={22} />
                  <span className="truncate font-medium text-foreground">
                    {row.team.name}
                  </span>
                </div>
              </td>
              <NumCell value={row.played} hide="sm" />
              <NumCell value={row.won} hide="sm" />
              <NumCell value={row.drawn} hide="sm" />
              <NumCell value={row.lost} hide="sm" />
              <NumCell value={row.goals_for} hide="md" />
              <NumCell value={row.goals_against} hide="md" />
              <td className="px-3 py-2.5 text-center tabular-nums">
                <span
                  className={cn(
                    row.goal_difference > 0 && "text-accent",
                    row.goal_difference < 0 && "text-muted",
                  )}
                >
                  {row.goal_difference > 0 ? `+${row.goal_difference}` : row.goal_difference}
                </span>
              </td>
              <td className="px-3 py-2.5 text-center font-semibold tabular-nums text-foreground">
                {row.points}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NumCell({ value, hide }: { value: number; hide: "sm" | "md" }) {
  return (
    <td
      className={cn(
        "px-3 py-2.5 text-center tabular-nums text-muted",
        hideClass[hide],
      )}
    >
      {value}
    </td>
  );
}
