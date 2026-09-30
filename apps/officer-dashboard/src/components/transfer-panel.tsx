"use client";

import { useState } from "react";
import { toast } from "sonner";
import { ArrowRight, Bell, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { TransferPill } from "@/components/bits";
import { apiPost } from "@/lib/api";
import { fmtDate, fmtNum, fmtPct } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Medicine, Notification, OptimizeResult, StateConfig, Transfer } from "@/lib/types";

const selectCls =
  "h-8 rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/50";

const STATUS_ORDER: Record<Transfer["status"], number> = { proposed: 0, approved: 1, dispatched: 2, received: 3, rejected: 4 };

type Action = "approve" | "reject" | "dispatch" | "receive";
const ACTION_DONE: Record<Action, string> = {
  approve: "approved; PHCs notified",
  reject: "rejected",
  dispatch: "marked dispatched",
  receive: "marked received",
};

interface Props {
  state: string;
  district: string;
  stateConfig: StateConfig | undefined;
  transfers: Transfer[] | undefined;
  medicines: Medicine[];
  notifications: Notification[] | undefined;
  onChanged: () => void;
  onSelectFacility: (id: string) => void;
}

export function travelSource(mode: string): string {
  if (mode === "haversine") return "straight-line estimate (demo)";
  if (mode === "routes_api") return "Google Routes API";
  return mode;
}

export function TransferPanel({ state, district, stateConfig, transfers, medicines, notifications, onChanged, onSelectFacility }: Props) {
  const [drug, setDrug] = useState("");
  const [maxMinutes, setMaxMinutes] = useState(120);
  const [crossDistrict, setCrossDistrict] = useState(false);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [filter, setFilter] = useState<"open" | "all" | Transfer["status"]>("all");
  const [busy, setBusy] = useState<string | null>(null);

  const tracers = medicines.filter((m) => m.is_tracer);
  const medName = new Map(medicines.map((m) => [m.drug_code, m.name]));
  const allowCross = stateConfig?.cross_district_transfers ?? false;

  async function optimise() {
    setRunning(true);
    try {
      const r = await apiPost<OptimizeResult>("/api/redistribution/optimize", {
        state,
        district,
        drug_code: drug || undefined,
        max_travel_minutes: maxMinutes,
        target_cover_days: 30,
        allow_cross_district: allowCross && crossDistrict,
      });
      setResult(r);
      toast.success(`Optimiser proposed ${r.transfers.length} transfer${r.transfers.length === 1 ? "" : "s"} for review`);
      onChanged();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  async function act(t: Transfer, action: Action) {
    setBusy(t.transfer_id);
    try {
      await apiPost<Transfer>(`/api/transfers/${t.transfer_id}/${action}`, { by: "District Health Officer" });
      toast.success(`${t.quantity} ${t.unit}s ${t.medicine}: ${ACTION_DONE[action]}`);
      onChanged();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  const list = (transfers ?? [])
    .filter((t) =>
      filter === "all" ? true : filter === "open" ? ["proposed", "approved", "dispatched"].includes(t.status) : t.status === filter,
    )
    .sort((a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status] || b.created_at.localeCompare(a.created_at));
  const counts = (transfers ?? []).reduce<Record<string, number>>((acc, t) => ({ ...acc, [t.status]: (acc[t.status] ?? 0) + 1 }), {});

  return (
    <div className="flex flex-col gap-3">
      {/* Optimiser controls */}
      <div className="rounded-lg border bg-muted/30 p-3">
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex min-w-0 flex-col gap-1 text-xs text-muted-foreground">
            Medicine
            <select className={cn(selectCls, "max-w-[14rem]")} value={drug} onChange={(e) => setDrug(e.target.value)}>
              <option value="">All tracer medicines</option>
              {tracers.map((m) => (
                <option key={m.drug_code} value={m.drug_code}>
                  {m.name} {m.strength}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Max travel
            <select className={selectCls} value={maxMinutes} onChange={(e) => setMaxMinutes(Number(e.target.value))}>
              {[60, 90, 120, 180].map((m) => (
                <option key={m} value={m}>
                  {m} min
                </option>
              ))}
            </select>
          </label>
          {allowCross && (
            <label className="flex h-8 items-center gap-1.5 text-xs">
              <input type="checkbox" checked={crossDistrict} onChange={(e) => setCrossDistrict(e.target.checked)} />
              Cross-district
            </label>
          )}
          <Button onClick={optimise} disabled={running}>
            <Sparkles />
            {running ? "Optimising…" : "Run optimiser"}
          </Button>
        </div>
        <p className="mt-1.5 text-[11px] text-muted-foreground">
          Target 30 days of cover; donors keep their safety stock. Cross-district transfers are{" "}
          {allowCross ? "allowed by state policy" : "disabled by state policy"}. Every transfer needs DHO approval.
        </p>
        {result && (
          <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 rounded-md border bg-background p-2 text-xs sm:grid-cols-4">
            <div>
              <div className="text-muted-foreground">Receivers</div>
              <div className="font-semibold">{result.summary.receivers}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Donors</div>
              <div className="font-semibold">{result.summary.donors}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Candidates</div>
              <div className="font-semibold">{result.summary.total_candidates}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Proposed</div>
              <div className="font-semibold">{result.transfers.length}</div>
            </div>
            <div className="col-span-2 sm:col-span-4">
              <span className="text-muted-foreground">Unmet need after transfers: </span>
              {Object.keys(result.summary.unmet_need).length === 0
                ? "none"
                : Object.entries(result.summary.unmet_need)
                    .map(([code, q]) => `${medName.get(code) ?? code} ${fmtNum(q)}`)
                    .join(" · ")}
              {Object.keys(result.summary.unmet_need).length > 0 && (
                <span className="text-muted-foreground"> (needs warehouse supply)</span>
              )}
            </div>
            <div className="col-span-2 text-muted-foreground sm:col-span-4">
              Solver: {result.summary.solver} · Travel time:{" "}
              <span className={result.summary.travel_mode === "haversine" ? "text-amber-700 dark:text-amber-400" : ""}>
                {travelSource(result.summary.travel_mode)}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Transfer list */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-xs text-muted-foreground">
          {Object.entries(counts)
            .map(([s, n]) => `${n} ${s}`)
            .join(" · ") || "No transfers yet. Run the optimiser."}
        </div>
        <select className={selectCls} value={filter} onChange={(e) => setFilter(e.target.value as typeof filter)} aria-label="Filter transfers">
          <option value="all">All transfers</option>
          <option value="open">Open (proposed → dispatched)</option>
          <option value="proposed">Proposed</option>
          <option value="approved">Approved</option>
          <option value="dispatched">Dispatched</option>
          <option value="received">Received</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      {!transfers ? (
        <Skeleton className="h-40" />
      ) : (
        <div className="flex max-h-[900px] flex-col gap-2 overflow-y-auto pr-0.5">
          {list.map((t) => (
            <TransferCard key={t.transfer_id} t={t} busy={busy === t.transfer_id} onAct={act} onSelectFacility={onSelectFacility} />
          ))}
        </div>
      )}

      {/* DHO notifications */}
      <div>
        <div className="mb-1 flex items-center gap-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">
          <Bell className="size-3.5" /> DHO notifications
        </div>
        {!notifications ? (
          <Skeleton className="h-12" />
        ) : notifications.length === 0 ? (
          <p className="text-xs text-muted-foreground">No notifications yet.</p>
        ) : (
          <ul className="max-h-48 space-y-1 overflow-y-auto text-xs">
            {[...notifications]
              .sort((a, b) => b.created_at.localeCompare(a.created_at))
              .slice(0, 20)
              .map((n) => (
                <li key={n.notification_id} className="rounded border px-2 py-1">
                  <span className="text-muted-foreground">{fmtDate(n.created_at)} · </span>
                  {n.texts.en ?? Object.values(n.texts)[0]}
                </li>
              ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function Cover({ label, before, after, extra }: { label: string; before: number; after: number; extra?: string }) {
  return (
    <div>
      <div className="text-muted-foreground">{label}</div>
      <div className="font-medium tabular-nums">
        {fmtNum(before, 1)} → {fmtNum(after, 1)} d{extra && <span className="font-normal text-muted-foreground"> {extra}</span>}
      </div>
    </div>
  );
}

function TransferCard({
  t,
  busy,
  onAct,
  onSelectFacility,
}: {
  t: Transfer;
  busy: boolean;
  onAct: (t: Transfer, a: Action) => void;
  onSelectFacility: (id: string) => void;
}) {
  const o = t.optimiser;
  const e = t.explanation;
  const demoAi = t.is_demo || t.ai_mode !== "gemini";
  return (
    <div className={cn("rounded-lg border p-3 text-sm", t.status === "proposed" && "border-amber-300 dark:border-amber-800", t.status === "rejected" && "opacity-60")}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 font-semibold">
          Move {fmtNum(t.quantity)} {t.unit}s {t.medicine}
        </div>
        <TransferPill status={t.status} />
      </div>
      <div className="mt-0.5 flex flex-wrap items-center gap-1 text-xs">
        <button type="button" className="font-medium underline-offset-2 hover:underline" onClick={() => onSelectFacility(t.from_facility_id)}>
          {t.from_name}
        </button>
        <ArrowRight className="size-3" />
        <button type="button" className="font-medium underline-offset-2 hover:underline" onClick={() => onSelectFacility(t.to_facility_id)}>
          {t.to_name}
        </button>
        <span className="text-muted-foreground">
          · ~{Math.round(t.travel_minutes)} min ({travelSource(t.travel_mode)}){t.cross_district && " · cross-district"}
        </span>
      </div>

      <div className="mt-2 grid grid-cols-2 gap-2 rounded-md bg-muted/40 p-2 text-xs sm:grid-cols-4">
        <div>
          <div className="text-muted-foreground">Stock-out days avoided</div>
          <div className="font-semibold text-emerald-700 tabular-nums dark:text-emerald-400">{fmtNum(o.stockout_days_avoided, 1)}</div>
        </div>
        <div>
          <div className="text-muted-foreground">Receiver risk</div>
          <div className="font-medium tabular-nums">{fmtPct(o.receiver_stockout_risk)}</div>
        </div>
        <Cover label="Receiver cover" before={o.receiver_cover_before} after={o.receiver_cover_after} />
        <Cover label="Donor cover" before={o.donor_cover_before} after={o.donor_cover_after} extra={`(safety ${o.donor_safety_days})`} />
        {o.donor_near_expiry_qty > 0 && (
          <div className="col-span-2 text-amber-800 sm:col-span-4 dark:text-amber-300">
            Donor has {fmtNum(o.donor_near_expiry_qty)} near-expiry units
            {o.donor_near_expiry_date ? ` (expiring ${o.donor_near_expiry_date})` : ""}: moving them reduces wastage.
          </div>
        )}
      </div>

      <details className="mt-2 rounded-md border px-2 py-1.5 text-xs" open={t.status === "proposed"}>
        <summary className="cursor-pointer font-medium">
          AI explanation <span className="font-normal text-muted-foreground">· confidence {fmtPct(e.confidence)}</span>
          {demoAi && (
            <span className="ml-1.5 rounded bg-violet-100 px-1 py-0.5 text-[10px] font-medium text-violet-900 dark:bg-violet-900/40 dark:text-violet-100">
              Demo AI
            </span>
          )}
        </summary>
        <div className="mt-1.5 space-y-1.5">
          <p>{e.summary}</p>
          <ul className="list-disc space-y-0.5 pl-4">
            {e.reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
          <p>
            <span className="font-medium">Impact: </span>
            {e.impact}
          </p>
          {e.uncertainties.length > 0 && (
            <div>
              <span className="font-medium">Uncertainties:</span>
              <ul className="list-disc pl-4 text-muted-foreground">
                {e.uncertainties.map((u) => (
                  <li key={u}>{u}</li>
                ))}
              </ul>
            </div>
          )}
          <p className="text-[10px] text-muted-foreground">
            {t.model_name} · {t.model_version} · {t.prompt_version} · AI mode: {t.ai_mode}. Recommendation only; requires human approval.
          </p>
        </div>
      </details>

      <ol className="mt-2 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-muted-foreground">
        {t.history.map((h, i) => (
          <li key={`${h.status}-${i}`} className="flex items-center gap-1">
            <span className={cn("inline-block size-1.5 rounded-full", h.status === "rejected" ? "bg-muted-foreground" : "bg-primary")} />
            <span className="font-medium text-foreground">{h.status}</span> {fmtDate(h.at)} · {h.by}
            {h.note && h.status !== "proposed" ? ` · ${h.note}` : ""}
          </li>
        ))}
      </ol>

      <div className="mt-2 flex flex-wrap gap-2">
        {t.status === "proposed" && (
          <>
            <Button size="sm" disabled={busy} onClick={() => onAct(t, "approve")}>
              Approve
            </Button>
            <Button size="sm" variant="outline" disabled={busy} onClick={() => onAct(t, "reject")}>
              Reject
            </Button>
          </>
        )}
        {t.status === "approved" && (
          <Button size="sm" variant="secondary" disabled={busy} onClick={() => onAct(t, "dispatch")}>
            Mark dispatched
          </Button>
        )}
        {t.status === "dispatched" && (
          <>
            <Button size="sm" variant="secondary" disabled={busy} onClick={() => onAct(t, "receive")}>
              Mark received
            </Button>
            <span className="self-center text-[11px] text-muted-foreground">Normally confirmed by the receiving PHC.</span>
          </>
        )}
      </div>
    </div>
  );
}
