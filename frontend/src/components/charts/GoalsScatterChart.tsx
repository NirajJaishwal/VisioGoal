"use client";

import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import { ChartCard, chartColors } from "@/components/charts/ChartCard";
import { useTheme } from "@/lib/theme";
import type { Standing } from "@/types/api";

type Datum = { x: number; y: number; name: string };

/** Goals For (x) vs Goals Against (y), one point per team. */
export function GoalsScatterChart({ standings }: { standings: Standing[] }) {
  const { theme } = useTheme();
  const colors = chartColors(theme === "dark");

  const data: Datum[] = standings.map((s) => ({
    x: s.goals_for,
    y: s.goals_against,
    name: s.team.name,
  }));

  return (
    <ChartCard title="Goals For vs Goals Against" subtitle="Attack vs defense">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 8, right: 12, left: -16, bottom: 4 }}>
          <CartesianGrid stroke={colors.grid} />
          <XAxis
            type="number"
            dataKey="x"
            name="Goals For"
            tick={{ fill: colors.tick, fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: colors.grid }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="Goals Against"
            tick={{ fill: colors.tick, fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: colors.grid }}
          />
          <ZAxis range={[60, 60]} />
          <Tooltip cursor={{ strokeDasharray: "3 3" }} content={<GoalsTooltip />} />
          <Scatter data={data} fill={colors.accent} fillOpacity={0.75} />
        </ScatterChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

function GoalsTooltip({
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
      <p className="font-medium text-foreground">{d.name}</p>
      <p className="text-muted">
        {d.x} scored · {d.y} conceded
      </p>
    </div>
  );
}
