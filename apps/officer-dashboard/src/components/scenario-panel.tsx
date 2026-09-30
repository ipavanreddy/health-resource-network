"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { FlaskConical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiPost } from "@/lib/api";
import { fmtNum, fmtPct } from "@/lib/format";
import type { Medicine } from "@/lib/types";

interface ScenarioWeek {
  week: number;
  week_start: string;
  baseline_stocked_out: number;
  scenario_stocked_out: number;
  scenario_shortfall_units: number;
}

interface ScenarioResult {
  scope: { state: string; district: string | null; facilities: number };
  drug_codes: string[];
  multiplier: number;
  duration_weeks: number;
  weeks: ScenarioWeek[];
  facilities_at_risk: {
    facility_id: string;
    name: string;
    block: string;
    medicine: string;
    unit: string;
    available: number;
    baseline_stockout_week: number | null;
    scenario_stockout_week: number;
    shortfall_units: number;
  }[];
  facilities_at_risk_total: number;
  redistribution: { shortfall_units: number; surplus_units_in_scope: number; coverable_share: number; note: string };
  method: string;
}

const sel =
  "h-8 min-w-0 rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/50";

/** Emergency scenario view (PRD §15.3, FR-11): what-if demand multiplier → projected stock-outs by week. */
export function ScenarioPanel({
  state,
  district,
  medicines,
  defaultGroup,
}: {
  state: string;
  district: string;
  medicines: Medicine[];
  defaultGroup?: string;
}) {
  const groups = useMemo(() => [...new Set(medicines.filter((m) => m.is_tracer).map((m) => m.group))], [medicines]);
  const [group, setGroup] = useState(defaultGroup ?? "fever");
  const [multiplier, setMultiplier] = useState(3);
  const [weeks, setWeeks] = useState(4);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ScenarioResult | null>(null);

  async function run() {
    setBusy(true);
    try {
      setResult(
        await apiPost<ScenarioResult>("/api/scenarios/simulate", { state, district, group, multiplier, duration_weeks: weeks }),
      );
    } catch (e) {
      toast.error(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const max = Math.max(1, ...(result?.weeks.map((w) => w.scenario_stocked_out) ?? [1]));
  const names = result?.drug_codes.map((c) => medicines.find((m) => m.drug_code === c)?.name ?? c).join(" + ");

  return (
    <div className="flex flex-col gap-3 text-sm">
      <div className="flex flex-wrap items-end gap-2">
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
          Medicine group
          <select className={sel} value={group} onChange={(e) => setGroup(e.target.value)}>
            {groups.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
          Demand multiplier
          <select className={sel} value={multiplier} onChange={(e) => setMultiplier(Number(e.target.value))}>
            {[1.5, 2, 3, 4, 5].map((m) => (
              <option key={m} value={m}>
                {m}× normal
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted-foreground">
          For
          <select className={sel} value={weeks} onChange={(e) => setWeeks(Number(e.target.value))}>
            {[2, 4, 6, 8].map((w) => (
              <option key={w} value={w}>
                {w} weeks
              </option>
            ))}
          </select>
        </label>
        <Button size="sm" onClick={run} disabled={busy || !district}>
          <FlaskConical /> {busy ? "Simulating…" : "Simulate"}
        </Button>
      </div>
      <p className="text-xs text-muted-foreground">What-if only: nothing is saved, and no alert or transfer is created.</p>

      {result && (
        <>
          <p>
            <span className="font-medium">{names}</span> at {result.multiplier}× for {result.duration_weeks} weeks across{" "}
            {result.scope.facilities} facilities: <span className="font-semibold text-destructive">{result.facilities_at_risk_total}</span>{" "}
            facility × medicine pairs stock out within 8 weeks.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-xs">
              <thead className="text-left text-muted-foreground">
                <tr>
                  <th className="px-2 py-1 font-medium">Week of</th>
                  <th className="px-2 py-1 font-medium">Stocked out: normal demand</th>
                  <th className="px-2 py-1 font-medium">Stocked out: scenario</th>
                  <th className="px-2 py-1 text-right font-medium">New shortfall (units)</th>
                </tr>
              </thead>
              <tbody>
                {result.weeks.map((w) => (
                  <tr key={w.week} className="border-t">
                    <td className="px-2 py-1 whitespace-nowrap">{new Date(w.week_start).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</td>
                    <td className="px-2 py-1 tabular-nums">{w.baseline_stocked_out}</td>
                    <td className="px-2 py-1">
                      <span className="inline-flex items-center gap-2">
                        <span className="inline-block h-2.5 rounded-sm bg-red-500/80" style={{ width: `${(w.scenario_stocked_out / max) * 120}px` }} />
                        <span className="tabular-nums font-medium">{w.scenario_stocked_out}</span>
                      </span>
                    </td>
                    <td className="px-2 py-1 text-right tabular-nums">{fmtNum(w.scenario_shortfall_units)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="rounded-md bg-muted/60 p-2 text-xs">
            <span className="font-medium">What redistribution can cover: </span>
            {fmtPct(result.redistribution.coverable_share)} of the {fmtNum(result.redistribution.shortfall_units)}-unit shortfall (surplus in scope:{" "}
            {fmtNum(result.redistribution.surplus_units_in_scope)} units). {result.redistribution.coverable_share < 0.5 && "The rest needs a warehouse or state indent. "}
            {result.redistribution.note}
          </p>
          {result.facilities_at_risk.length > 0 && (
            <div className="text-xs">
              <div className="mb-1 font-medium">Earliest stock-outs</div>
              <ul className="space-y-0.5">
                {result.facilities_at_risk.slice(0, 6).map((r) => (
                  <li key={`${r.facility_id}-${r.medicine}`}>
                    {r.name} ({r.block}) · {r.medicine}: week {r.scenario_stockout_week}
                    {r.baseline_stockout_week == null ? " (none under normal demand)" : r.baseline_stockout_week !== r.scenario_stockout_week ? ` (normal: week ${r.baseline_stockout_week})` : ""}{" "}
                    · short {fmtNum(r.shortfall_units)} {r.unit}s
                  </li>
                ))}
              </ul>
            </div>
          )}
          <p className="text-[11px] text-muted-foreground">{result.method} Synthetic data.</p>
        </>
      )}
    </div>
  );
}
