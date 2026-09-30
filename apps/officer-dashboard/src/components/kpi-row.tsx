import type { ReactNode } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { fmtNum, readinessColor } from "@/lib/format";
import type { Overview } from "@/lib/types";

function Tile({
  label,
  value,
  sub,
  tone,
  accent,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  tone?: "bad" | "warn";
  accent?: string;
}) {
  return (
    <div
      className={cn(
        "min-w-0 rounded-lg border bg-card px-3 py-2",
        tone === "bad" && "border-red-300 bg-red-50/60 dark:border-red-900 dark:bg-red-950/30",
        tone === "warn" && "border-amber-300 bg-amber-50/60 dark:border-amber-900 dark:bg-amber-950/30",
      )}
    >
      <div className="truncate text-[11px] font-medium tracking-wide text-muted-foreground uppercase">{label}</div>
      <div className="text-xl font-semibold tabular-nums" style={accent ? { color: accent } : undefined}>
        {value}
      </div>
      {sub && <div className="truncate text-[11px] text-muted-foreground">{sub}</div>}
    </div>
  );
}

export function KpiRow({ overview }: { overview: Overview | undefined }) {
  if (!overview) {
    return (
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5 2xl:grid-cols-9">
        {Array.from({ length: 9 }, (_, i) => (
          <Skeleton key={i} className="h-[68px]" />
        ))}
      </div>
    );
  }
  const o = overview;
  const topDrugs = o.at_risk_by_drug
    .slice(0, 3)
    .map((d) => `${d.name} (${d.facilities})`)
    .join(", ");
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5 2xl:grid-cols-9">
      <Tile
        label="Avg readiness"
        value={o.avg_readiness == null ? "–" : fmtNum(o.avg_readiness, 1)}
        sub="0–100, dispensing facilities"
        accent={readinessColor(o.avg_readiness)}
      />
      <Tile
        label="Reporting (24 h)"
        value={`${o.reporting_24h}/${o.facilities}`}
        sub={<span className={o.stale_72h > 0 ? "text-red-600 dark:text-red-400" : ""}>{o.stale_72h} stale &gt;72 h</span>}
        tone={o.stale_72h > 0 ? "warn" : undefined}
      />
      <Tile
        label="Stock-out risk"
        value={o.facilities_at_risk}
        sub="facilities high-risk / out"
        tone={o.facilities_at_risk > 0 ? "bad" : undefined}
      />
      <Tile label="Medicines at risk" value={o.medicines_at_risk} sub={topDrugs || "none"} tone={o.medicines_at_risk > 0 ? "warn" : undefined} />
      <Tile label="Beds available" value={`${fmtNum(o.beds_available)}/${fmtNum(o.beds_total)}`} sub="available / total" />
      <Tile label="Staff present" value={`${fmtNum(o.staff_present)}/${fmtNum(o.staff_sanctioned)}`} sub="present / sanctioned" />
      <Tile label="Surge signals" value={o.surge_alerts} sub="possible, to verify" tone={o.surge_alerts > 0 ? "bad" : undefined} />
      <Tile
        label="Pending transfers"
        value={o.pending_transfers}
        sub={`${o.active_transfers} active (approved / in transit)`}
        tone={o.pending_transfers > 0 ? "warn" : undefined}
      />
      <Tile label="Near-expiry units" value={fmtNum(o.near_expiry_qty)} sub="expiring < 90 days" />
    </div>
  );
}
