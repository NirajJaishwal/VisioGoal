"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard, chartColors } from "@/components/charts/ChartCard";
import { useTheme } from "@/lib/theme";
import type { Standing } from "@/types/api";

type Datum = { name: string; fullName: string; points: number };

/** Top 10 teams by points. */
export function PointsBarChart({ standings }: { standings: Standing[] }) {
  const { theme } = useTheme();
  const colors = chartColors(theme === "dark");

  const data: Datum[] = [...standings]
    .sort((a, b) => b.points - a.points)
    .slice(0, 10)
    .map((s) => ({
      name: s.team.short_name || s.team.name.slice(0, 3).toUpperCase(),
      fullName: s.team.name,
      points: s.points,
    }));

  return (
    <ChartCard title="Top 10 Teams by Points" subtitle="Current season">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke={colors.grid} />
          <XAxis
            dataKey="name"
            tick={{ fill: colors.tick, fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: colors.grid }}
            interval={0}
          />
          <YAxis
            tick={{ fill: colors.tick, fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            allowDecimals={false}
          />
          <Tooltip
            cursor={{ fill: colors.accent, fillOpacity: 0.08 }}
            content={<PointsTooltip />}
          />
          <Bar dataKey="points" fill={colors.accent} radius={[4, 4, 0, 0]} maxBarSize={44} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

function PointsTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: Datum }>;
}) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-lg border border-border bg-surface px-3 py-2 text-sm shadow-sm">
      <p className="font-medium text-foreground">{d.fullName}</p>
      <p className="text-muted">{d.points} pts</p>
    </div>
  );
}
