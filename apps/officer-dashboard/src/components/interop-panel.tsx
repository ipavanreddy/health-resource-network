"use client";

import type { ReactNode } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { SyntheticNote } from "@/components/bits";
import { useApi } from "@/lib/use-api";
import { fmtNum, fmtPct, readinessColor } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ModelCard, SampleExport, StateAnalytics, StateConfig } from "@/lib/types";

const WEIGHT_LABEL: Record<string, string> = {
  stock_cover: "Stock cover",
  beds: "Beds",
  staff: "Staff",
  freshness: "Freshness",
  surge_stability: "Surge stability",
};

function Panel({ title, sub, children, className }: { title: string; sub?: string; children: ReactNode; className?: string }) {
  return (
    <section className={cn("flex min-w-0 flex-col gap-2 rounded-lg border bg-card p-3", className)}>
      <div>
        <h2 className="font-semibold">{title}</h2>
        {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
      </div>
      {children}
    </section>
  );
}

function StateCard({ s, active }: { s: StateConfig; active: boolean }) {
  return (
    <div className={cn("flex min-w-0 flex-col gap-1.5 rounded-lg border p-3 text-xs", active && "border-primary ring-1 ring-primary/30")}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-semibold">
          {s.name} <span className="text-muted-foreground">({s.id})</span>
        </span>
        {active && <span className="rounded bg-primary px-1.5 py-0.5 text-[10px] text-primary-foreground">selected</span>}
      </div>
      <div>
        <span className="text-muted-foreground">Season focus: </span>
        {s.season_focus}
      </div>
      <div>
        <span className="text-muted-foreground">Languages: </span>
        {s.languages.join(", ")} (default {s.default_language})
      </div>
      <div>
        <span className="text-muted-foreground">Districts: </span>
        {s.districts.map((d) => d.name).join(", ")}
      </div>
      <div>
        <span className="text-muted-foreground">Cross-district transfers: </span>
        <span className={s.cross_district_transfers ? "text-emerald-700 dark:text-emerald-400" : ""}>
          {s.cross_district_transfers ? "allowed" : "not allowed"}
        </span>
      </div>
      <div>
        <div className="text-muted-foreground">Readiness weights</div>
        <div className="mt-0.5 flex h-3 overflow-hidden rounded">
          {Object.entries(s.readiness_weights).map(([k, w], i) => (
            <div
              key={k}
              title={`${WEIGHT_LABEL[k] ?? k}: ${w}`}
              style={{ width: `${w}%`, background: ["#2563eb", "#0891b2", "#7c3aed", "#d97706", "#dc2626"][i % 5] }}
            />
          ))}
        </div>
        <div className="mt-0.5 flex flex-wrap gap-x-2 text-[10px] text-muted-foreground">
          {Object.entries(s.readiness_weights).map(([k, w]) => (
            <span key={k}>
              {WEIGHT_LABEL[k] ?? k} {w}
            </span>
          ))}
        </div>
      </div>
      <div className="rounded bg-muted/50 p-1.5">
        <code className="text-[11px] font-semibold">{s.adapter.adapter_id}</code>
        <p className="text-[11px] text-muted-foreground">{s.adapter.description}</p>
      </div>
      <div className="text-[11px] text-muted-foreground">Forecast model: {s.forecast_model}</div>
    </div>
  );
}

function Json({ value }: { value: unknown }) {
  return (
    <pre className="max-h-72 overflow-auto rounded bg-muted/60 p-2 text-[11px] leading-snug">{JSON.stringify(value, null, 2)}</pre>
  );
}

export function InteropPanel({ states, stateId }: { states: StateConfig[]; stateId: string }) {
  const sample = useApi<SampleExport>(`/api/states/${stateId}/sample-export`);
  const analytics = useApi<StateAnalytics>(`/api/states/${stateId}/analytics`);
  const card = useApi<ModelCard>("/api/models/phc-demand-baseline/card");
  const arima = useApi<ArimaCard>("/api/models/weekly_demand_arima/card");
  const stateName = states.find((s) => s.id === stateId)?.name ?? stateId;

  return (
    <div className="flex flex-col gap-4">
      <SyntheticNote />
      <Panel title="State configurations" sub="One platform, per-state configuration: adapters, readiness weights, languages and transfer policy.">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {states.map((s) => (
            <StateCard key={s.id} s={s} active={s.id === stateId} />
          ))}
        </div>
      </Panel>

      <Panel
        title={`${stateName}: native record → canonical record`}
        sub="The state adapter maps the state's own export format onto the shared canonical schema (canonical-v1). Illustrative synthetic formats."
      >
        {!sample.data ? (
          <Skeleton className="h-48" />
        ) : (
          <>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
              <span>
                Adapter <code className="font-semibold">{sample.data.adapter.adapter_id}</code>
              </span>
              <span className="text-muted-foreground">
                facility key <code>{sample.data.adapter.facility_key}</code> · timestamp{" "}
                <code>{sample.data.adapter.timestamp.fields.join(" + ")}</code> ({sample.data.adapter.timestamp.format})
              </span>
              {Object.keys(sample.data.adapter.unit_factors).length > 0 && (
                <span className="text-muted-foreground">
                  unit factors:{" "}
                  {Object.entries(sample.data.adapter.unit_factors)
                    .map(([k, v]) => `${k} ×${v}`)
                    .join(", ")}
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-1 text-[11px]">
              {Object.entries(sample.data.adapter.fields).map(([canon, native]) => (
                <span key={canon} className="rounded border px-1.5 py-0.5">
                  <code>{native}</code> → <code className="font-semibold">{canon}</code>
                </span>
              ))}
            </div>
            <div className="flex flex-col gap-3">
              {sample.data.records.slice(0, 2).map((r, i) => (
                <div key={i} className="grid min-w-0 gap-2 md:grid-cols-2">
                  <div className="min-w-0">
                    <div className="mb-0.5 text-[11px] font-medium text-muted-foreground">Native ({stateId} export)</div>
                    <Json value={r.native} />
                  </div>
                  <div className="min-w-0">
                    <div className="mb-0.5 text-[11px] font-medium text-muted-foreground">Canonical (shared schema)</div>
                    <Json value={r.canonical} />
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </Panel>

      <Panel title={`${stateName}: district analytics`} sub="Aggregates computed from canonical records; only aggregates are shared across states.">
        {!analytics.data ? (
          <Skeleton className="h-32" />
        ) : (
          <div className="overflow-x-auto rounded border">
            <table className="w-full text-xs">
              <thead className="bg-muted/50 text-muted-foreground">
                <tr>
                  {["District", "Facilities", "Avg readiness", "Reporting 24 h", "Stale >72 h", "At risk", "Beds free", "Staff present", "Surge signals", "Transfers (pending / active)"].map((h) => (
                    <th key={h} className="px-2 py-1 text-left font-medium whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y">
                {[...analytics.data.districts.map((d) => ({ label: d.name, o: d, total: false })), { label: "State total", o: analytics.data.overall, total: true }].map(
                  ({ label, o, total }) => (
                    <tr key={label} className={cn(total && "bg-muted/30 font-semibold")}>
                      <td className="px-2 py-1 whitespace-nowrap">{label}</td>
                      <td className="px-2 py-1 tabular-nums">{o.facilities}</td>
                      <td className="px-2 py-1 tabular-nums" style={{ color: readinessColor(o.avg_readiness) }}>
                        {fmtNum(o.avg_readiness, 1)}
                      </td>
                      <td className="px-2 py-1 tabular-nums">
                        {o.reporting_24h}/{o.facilities}
                      </td>
                      <td className={cn("px-2 py-1 tabular-nums", o.stale_72h > 0 && "text-red-600")}>{o.stale_72h}</td>
                      <td className="px-2 py-1 tabular-nums">{o.facilities_at_risk}</td>
                      <td className="px-2 py-1 tabular-nums">
                        {o.beds_available}/{o.beds_total}
                      </td>
                      <td className="px-2 py-1 tabular-nums">
                        {o.staff_present}/{o.staff_sanctioned}
                      </td>
                      <td className="px-2 py-1 tabular-nums">{o.surge_alerts}</td>
                      <td className="px-2 py-1 tabular-nums">
                        {o.pending_transfers} / {o.active_transfers}
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <Panel title="Shared forecast model card" sub="Same base model runs for every state on canonical features; each state publishes its own accuracy back.">
        {!card.data ? (
          <Skeleton className="h-48" />
        ) : (
          <ModelCardView c={card.data} />
        )}
        {arima.data && (
          <div className="mt-3 rounded-md border border-dashed p-2 text-xs">
            <div className="font-medium">
              Challenger: <code>weekly_demand_arima</code> · BigQuery ML ARIMA_PLUS · <span className="text-muted-foreground">{arima.data.status}</span>
            </div>
            {arima.data.training_summary ? (
              <p className="text-muted-foreground">
                {arima.data.training_summary.series.toLocaleString("en-IN")} facility × medicine series trained in BigQuery ML
                {arima.data.training_summary.trained_at ? ` on ${arima.data.training_summary.trained_at.slice(0, 10)}` : ""} ·{" "}
                {arima.data.training_summary.series_with_seasonality.toLocaleString("en-IN")} with seasonality · median AIC{" "}
                {arima.data.training_summary.median_aic}. {arima.data.note}
              </p>
            ) : (
              <p className="text-muted-foreground">{arima.data.summary}</p>
            )}
          </div>
        )}
      </Panel>
    </div>
  );
}

interface ArimaCard {
  id: string;
  summary: string;
  status: string;
  note?: string;
  training_summary?: { series: number; trained_at: string | null; median_aic: number; series_with_seasonality: number } | null;
}

function ModelCardView({ c }: { c: ModelCard }) {
  return (
    <div className="grid gap-4 text-xs lg:grid-cols-2">
      <div className="flex min-w-0 flex-col gap-2">
        <div>
          <div className="text-sm font-semibold">{c.name}</div>
          <div className="text-muted-foreground">
            <code>
              {c.id}@{c.version}
            </code>{" "}
            · {c.type}
          </div>
        </div>
        <div>
          <div className="font-medium">Features</div>
          <ul className="list-disc pl-4 text-muted-foreground">
            {c.features.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </div>
        <div>
          <span className="font-medium">Output: </span>
          {c.output} · horizon {c.horizon_weeks} weeks
        </div>
        <div>
          <div className="font-medium">Training scope</div>
          <p className="text-muted-foreground">
            {c.training_data_scope.dataset}
            {c.training_data_scope.is_synthetic && <span className="font-semibold text-amber-700 dark:text-amber-400"> (synthetic)</span>} ·{" "}
            {c.training_data_scope.history} · states {c.training_data_scope.states.join(", ")} · facility-level data leaves state:{" "}
            {c.training_data_scope.facility_level_data_leaves_state ? "yes" : "no"}
          </p>
        </div>
        <div>
          <span className="font-medium">Intended use: </span>
          {c.intended_use}
        </div>
        <div>
          <span className="font-medium">Registry: </span>
          <span className="text-muted-foreground">{c.registry}</span>
        </div>
      </div>
      <div className="flex min-w-0 flex-col gap-2">
        <div>
          <div className="font-medium">Evaluation</div>
          <p className="text-muted-foreground">{c.evaluation.metric}</p>
        </div>
        <div className="overflow-x-auto rounded border">
          <table className="w-full">
            <thead className="bg-muted/50 text-muted-foreground">
              <tr>
                <th className="px-2 py-1 text-left font-medium">State</th>
                <th className="px-2 py-1 text-right font-medium">Model</th>
                <th className="px-2 py-1 text-right font-medium">Same week last yr</th>
                <th className="px-2 py-1 text-right font-medium">4-wk moving avg</th>
                <th className="px-2 py-1 text-right font-medium">Gain vs last yr</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {c.evaluation.per_state.map((p) => {
                const best = Math.min(p.wape_model, p.wape_same_week_last_year, p.wape_moving_average_4w);
                const cls = (v: number) => cn("px-2 py-1 text-right tabular-nums", v === best && "font-semibold text-emerald-700 dark:text-emerald-400");
                return (
                  <tr key={p.state}>
                    <td className="px-2 py-1">
                      {p.state_name}
                      <div className="text-[10px] text-muted-foreground">
                        {p.facilities} facilities · {p.series} series
                      </div>
                    </td>
                    <td className={cls(p.wape_model)}>{fmtPct(p.wape_model)}</td>
                    <td className={cls(p.wape_same_week_last_year)}>{fmtPct(p.wape_same_week_last_year)}</td>
                    <td className={cls(p.wape_moving_average_4w)}>{fmtPct(p.wape_moving_average_4w)}</td>
                    <td className="px-2 py-1 text-right tabular-nums">{fmtPct(p.improvement_vs_same_week_last_year)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-muted-foreground">WAPE: weighted absolute percentage error, lower is better. Best per state in green.</p>
        <p className="text-muted-foreground">{c.shared_use}</p>
        <div>
          <div className="font-medium">Limitations</div>
          <ul className="list-disc pl-4 text-muted-foreground">
            {c.limitations.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
