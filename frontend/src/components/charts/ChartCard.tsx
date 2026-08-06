import type { ReactNode } from "react";

/** Card shell shared by the charts: title, optional subtitle, fixed-height body. */
export function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4 sm:p-5">
      <div className="mb-3">
        <h3 className="font-semibold">{title}</h3>
        {subtitle && <p className="text-sm text-muted">{subtitle}</p>}
      </div>
      <div className="h-72 w-full">{children}</div>
    </div>
  );
}

/** Theme-aware colors for chart axes/grid (accent stays constant). */
export function chartColors(isDark: boolean) {
  return {
    accent: "#10b981",
    grid: isDark ? "#26313f" : "#e5eaf0",
    tick: isDark ? "#93a4b8" : "#64748b",
    tooltipBg: isDark ? "#141b25" : "#ffffff",
    tooltipBorder: isDark ? "#26313f" : "#e5eaf0",
  };
}
