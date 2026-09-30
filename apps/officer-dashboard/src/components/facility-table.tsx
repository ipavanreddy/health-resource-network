"use client";

import { useState } from "react";
import { ArrowDown, ArrowUp } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { ReadinessChip, StatusPill } from "@/components/bits";
import { fmtAgo } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { FacilitySummary, StockStatus } from "@/lib/types";

type SortKey = "name" | "block" | "type" | "readiness" | "status" | "risk" | "beds" | "staff" | "report";

const STATUS_RANK: Record<StockStatus, number> = { stocked_out: 0, critical: 1, low: 2, adequate: 3 };

const sortValue: Record<SortKey, (f: FacilitySummary) => number | string> = {
  name: (f) => f.name,
  block: (f) => f.block,
  type: (f) => f.type,
  readiness: (f) => f.readiness?.score ?? 999,
  status: (f) => (f.worst_status ? STATUS_RANK[f.worst_status] : 9),
  risk: (f) => riskDrugs(f).length,
  beds: (f) => (f.beds ? f.beds.total - f.beds.occupied : 0),
  staff: (f) => (f.staff && f.staff.sanctioned ? f.staff.present / f.staff.sanctioned : 0),
  report: (f) => f.freshness_hours ?? 9999,
};

function riskDrugs(f: FacilitySummary): string[] {
  return [...new Set([...(f.stocked_out ?? []), ...(f.high_risk ?? [])])];
}

const COLUMNS: { key: SortKey; label: string; className?: string }[] = [
  { key: "name", label: "Facility" },
  { key: "block", label: "Block", className: "hidden sm:table-cell" },
  { key: "type", label: "Type", className: "hidden md:table-cell" },
  { key: "readiness", label: "Readiness" },
  { key: "status", label: "Worst stock" },
  { key: "risk", label: "High-risk medicines", className: "hidden lg:table-cell" },
  { key: "beds", label: "Beds free", className: "hidden md:table-cell" },
  { key: "staff", label: "Staff", className: "hidden md:table-cell" },
  { key: "report", label: "Last report" },
];

interface Props {
  facilities: FacilitySummary[] | undefined;
  selectedId: string | null;
  onSelect: (id: string) => void;
  drugNames: Map<string, string>;
}

export function FacilityTable({ facilities, selectedId, onSelect, drugNames }: Props) {
  const [sort, setSort] = useState<{ key: SortKey; asc: boolean }>({ key: "readiness", asc: true });
  if (!facilities) return <Skeleton className="h-64" />;

  const rows = facilities
    .filter((f) => !f.is_warehouse)
    .sort((a, b) => {
      const va = sortValue[sort.key](a);
      const vb = sortValue[sort.key](b);
      const c = typeof va === "number" && typeof vb === "number" ? va - vb : String(va).localeCompare(String(vb));
      return sort.asc ? c : -c;
    });

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-xs text-muted-foreground">
          <tr>
            {COLUMNS.map((c) => (
              <th key={c.key} className={cn("px-2 py-1.5 text-left font-medium whitespace-nowrap", c.className)}>
                <button
                  type="button"
                  className="inline-flex items-center gap-0.5 hover:text-foreground"
                  onClick={() => setSort((s) => ({ key: c.key, asc: s.key === c.key ? !s.asc : true }))}
                >
                  {c.label}
                  {sort.key === c.key && (sort.asc ? <ArrowUp className="size-3" /> : <ArrowDown className="size-3" />)}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y">
          {rows.map((f) => {
            const risk = riskDrugs(f);
            return (
              <tr
                key={f.facility_id}
                onClick={() => onSelect(f.facility_id)}
                className={cn("cursor-pointer hover:bg-muted/60", f.facility_id === selectedId && "bg-primary/5 outline outline-1 -outline-offset-1 outline-primary/40")}
              >
                <td className="px-2 py-1.5">
                  <div className="font-medium">{f.name}</div>
                  <div className="text-[11px] text-muted-foreground sm:hidden">{f.block}</div>
                  {f.surge_groups && f.surge_groups.length > 0 && (
                    <div className="text-[11px] text-red-700 dark:text-red-400">possible surge: {f.surge_groups.join(", ")}</div>
                  )}
                </td>
                <td className="hidden px-2 py-1.5 sm:table-cell">{f.block}</td>
                <td className="hidden px-2 py-1.5 md:table-cell">{f.type}</td>
                <td className="px-2 py-1.5">
                  <ReadinessChip score={f.readiness?.score} band={f.readiness?.band} />
                </td>
                <td className="px-2 py-1.5">
                  <StatusPill status={f.worst_status} />
                </td>
                <td className="hidden max-w-[16rem] px-2 py-1.5 text-xs lg:table-cell">
                  {risk.length ? risk.map((c) => drugNames.get(c) ?? c).join(", ") : <span className="text-muted-foreground">–</span>}
                </td>
                <td className="hidden px-2 py-1.5 tabular-nums md:table-cell">
                  {f.beds ? `${f.beds.total - f.beds.occupied}/${f.beds.total}` : "–"}
                </td>
                <td className="hidden px-2 py-1.5 tabular-nums md:table-cell">{f.staff ? `${f.staff.present}/${f.staff.sanctioned}` : "–"}</td>
                <td className="px-2 py-1.5 text-xs whitespace-nowrap">
                  {f.stale ? (
                    <span className="font-semibold text-red-600 dark:text-red-400">stale · {fmtAgo(f.freshness_hours)}</span>
                  ) : (
                    fmtAgo(f.freshness_hours)
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
