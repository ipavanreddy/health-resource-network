"use client";

import { useEffect, useState, type ReactNode } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ReadinessChip, StatusPill, SyntheticNote } from "@/components/bits";
import { ForecastChart } from "@/components/forecast-chart";
import { useApi } from "@/lib/use-api";
import { RISK_CLASS, fmtAgo, fmtDate, fmtNum, fmtPct, readinessColor } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { FacilityDetail as FacilityDetailT, Forecast, Freshness, Readiness, StockRow } from "@/lib/types";

interface Props {
  facilityId: string;
  version: number;
  onClose: () => void;
}

function Section({ title, children, aside }: { title: string; children: ReactNode; aside?: ReactNode }) {
  return (
    <section className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{title}</h3>
        {aside}
      </div>
      {children}
    </section>
  );
}

function ReadinessBars({ r }: { r: Readiness }) {
  return (
    <div className="flex flex-col gap-2">
      {r.components.map((c) => (
        <div key={c.key} className="text-xs">
          <div className="flex justify-between gap-2">
            <span className="font-medium">
              {c.label} <span className="font-normal text-muted-foreground">· weight {c.weight}</span>
            </span>
            <span className="tabular-nums">
              {fmtNum(c.score, 0)}/100 <span className="text-muted-foreground">({fmtNum(c.points, 1)} pts)</span>
            </span>
          </div>
          <div className="mt-0.5 h-2 overflow-hidden rounded bg-muted">
            <div className="h-full rounded" style={{ width: `${Math.max(0, Math.min(100, c.score))}%`, background: readinessColor(c.score) }} />
          </div>
          <div className="text-[11px] text-muted-foreground">{c.detail}</div>
        </div>
      ))}
      <p className="text-[11px] text-muted-foreground">{r.method}</p>
    </div>
  );
}

function FreshnessGrid({ f }: { f: Freshness }) {
  const cell = (label: string, hours: number | null, sub: string) => (
    <div className={cn("rounded border px-2 py-1", hours != null && hours > 72 && "border-red-300 bg-red-50/60 dark:border-red-900 dark:bg-red-950/30")}>
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="text-xs font-medium">{hours == null ? sub : fmtAgo(hours)}</div>
      {hours != null && <div className="truncate text-[10px] text-muted-foreground">{sub}</div>}
    </div>
  );
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {cell("Stock", f.stock.hours_ago, `${f.stock.source} · ${fmtDate(f.stock.at)}`)}
      {cell("Beds", f.beds.hours_ago, fmtDate(f.beds.at))}
      {cell("Attendance", f.attendance.hours_ago, fmtDate(f.attendance.at))}
      {cell("Forecast", null, `${fmtDate(f.forecast.at)} · ${f.forecast.model}`)}
    </div>
  );
}

function StockTable({ rows }: { rows: StockRow[] }) {
  return (
    <div className="overflow-x-auto rounded border">
      <table className="w-full text-xs">
        <thead className="bg-muted/50 text-muted-foreground">
          <tr>
            <th className="px-2 py-1 text-left font-medium">Medicine</th>
            <th className="px-2 py-1 text-right font-medium">On hand</th>
            <th className="px-2 py-1 text-right font-medium">Daily</th>
            <th className="px-2 py-1 text-right font-medium">Cover</th>
            <th className="px-2 py-1 text-left font-medium">Status</th>
            <th className="px-2 py-1 text-right font-medium">Risk</th>
            <th className="px-2 py-1 text-left font-medium">Notes</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {rows.map((s) => (
            <tr key={s.drug_code}>
              <td className="px-2 py-1">
                <div className="font-medium">{s.name}</div>
                <div className="text-[10px] text-muted-foreground">
                  {s.strength} · {s.unit}
                  {s.is_tracer ? " · tracer" : ""}
                </div>
              </td>
              <td className="px-2 py-1 text-right tabular-nums">
                {fmtNum(s.on_hand)}
                {s.in_transit > 0 && <div className="text-[10px] text-muted-foreground">+{fmtNum(s.in_transit)} in transit</div>}
              </td>
              <td className="px-2 py-1 text-right tabular-nums">{fmtNum(s.daily_demand, 1)}</td>
              <td className="px-2 py-1 text-right tabular-nums">{s.days_of_cover == null ? "–" : `${fmtNum(s.days_of_cover, 1)} d`}</td>
              <td className="px-2 py-1">
                <StatusPill status={s.status} />
              </td>
              <td className={cn("px-2 py-1 text-right tabular-nums", RISK_CLASS[s.risk_band])}>{fmtPct(s.stockout_risk)}</td>
              <td className="px-2 py-1 text-[10px]">
                {s.surge && <div className="font-semibold text-red-700 dark:text-red-400">possible surge {s.surge_ratio.toFixed(1)}×</div>}
                {s.near_expiry_qty > 0 && (
                  <div className="text-amber-800 dark:text-amber-300">
                    {fmtNum(s.near_expiry_qty)} near expiry{s.near_expiry_date ? ` (${s.near_expiry_date})` : ""}
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function FacilityDetailPanel({ facilityId, version, onClose }: Props) {
  const base = `/api/facilities/${encodeURIComponent(facilityId)}`;
  const detail = useApi<FacilityDetailT>(base, version);
  const stock = useApi<{ stock: StockRow[]; freshness: Freshness }>(`${base}/stock`, version);
  const readiness = useApi<Readiness>(`${base}/readiness`, version);
  const [drug, setDrug] = useState<string | null>(null);

  const tracerRows = (stock.data?.stock ?? []).filter((s) => s.is_tracer);
  const defaultDrug = [...tracerRows].sort((a, b) => b.stockout_risk - a.stockout_risk || Number(b.surge) - Number(a.surge))[0]?.drug_code;
  const effectiveDrug = drug ?? defaultDrug ?? null;
  const forecast = useApi<{ forecasts: Forecast[] }>(
    effectiveDrug ? `${base}/forecast?drug_code=${encodeURIComponent(effectiveDrug)}` : null,
    version,
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const d = detail.data;
  const fc = forecast.data?.forecasts[0];

  return (
    <div className="fixed inset-0 z-[1100] flex justify-end" role="dialog" aria-modal="true" aria-label="Facility details">
      <button type="button" aria-label="Close details" className="absolute inset-0 bg-black/30" onClick={onClose} />
      <aside className="relative flex h-full w-full max-w-2xl flex-col overflow-y-auto border-l bg-background shadow-2xl">
        <header className="sticky top-0 z-10 flex items-start justify-between gap-2 border-b bg-background/95 px-4 py-3 backdrop-blur">
          <div className="min-w-0">
            <h2 className="truncate text-lg font-semibold">{d?.name ?? facilityId}</h2>
            {d && (
              <p className="text-xs text-muted-foreground">
                {d.type} · {d.block} block · {d.district_name} · HFR {d.hfr_id}
                {d.opd_today != null && ` · OPD today ${d.opd_today}`}
                {d.warehouse && ` · supplied by ${d.warehouse.name} (lead time ${d.lead_time_days} d)`}
              </p>
            )}
          </div>
          <Button variant="ghost" size="icon-sm" onClick={onClose} aria-label="Close">
            <X />
          </Button>
        </header>

        <div className="flex flex-col gap-5 p-4">
          {detail.error && <p className="text-sm text-destructive">{detail.error}</p>}
          <SyntheticNote />

          <Section title="Readiness" aside={d?.readiness && <ReadinessChip score={d.readiness.score} band={d.readiness.band} />}>
            {readiness.data ? <ReadinessBars r={readiness.data} /> : <Skeleton className="h-40" />}
          </Section>

          <Section title="Data freshness" aside={stock.data?.freshness.stale && <span className="text-xs font-semibold text-red-600">STALE (&gt;72 h)</span>}>
            {stock.data ? <FreshnessGrid f={stock.data.freshness} /> : <Skeleton className="h-14" />}
          </Section>

          <Section title="Stock">{stock.data ? <StockTable rows={stock.data.stock} /> : <Skeleton className="h-48" />}</Section>

          <Section
            title="Demand forecast"
            aside={
              tracerRows.length > 0 && (
                <select
                  className="h-7 rounded-md border border-input bg-background px-2 text-xs"
                  value={effectiveDrug ?? ""}
                  onChange={(e) => setDrug(e.target.value)}
                  aria-label="Forecast medicine"
                >
                  {tracerRows.map((s) => (
                    <option key={s.drug_code} value={s.drug_code}>
                      {s.name} {s.strength}
                    </option>
                  ))}
                </select>
              )
            }
          >
            {fc ? <ForecastChart forecast={fc} /> : forecast.error ? <p className="text-xs text-destructive">{forecast.error}</p> : <Skeleton className="h-52" />}
          </Section>
        </div>
      </aside>
    </div>
  );
}
