"use client";

import { useState } from "react";
import { toast } from "sonner";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiPost } from "@/lib/api";
import { fmtDate, fmtPct } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Alert, FacilitySummary } from "@/lib/types";

interface Props {
  alerts: Alert[] | undefined;
  facilities: FacilitySummary[];
  onSelectFacility: (id: string) => void;
  onChanged: () => void;
}

export function AlertsPanel({ alerts, facilities, onSelectFacility, onChanged }: Props) {
  const [busy, setBusy] = useState<string | null>(null);
  const names = new Map(facilities.map((f) => [f.facility_id, f.name]));

  if (!alerts) return <Skeleton className="h-48" />;
  const surges = alerts.filter((a) => a.type === "surge");
  const facilityAlerts = alerts
    .filter((a) => a.type !== "surge")
    .sort((a, b) => (a.type === b.type ? 0 : a.type === "stocked_out" ? -1 : 1));
  const models = [...new Set(alerts.map((a) => `${a.model_name} v${a.model_version}`))];

  async function review(a: Alert, action: "verify" | "dismiss") {
    setBusy(a.alert_id);
    try {
      await apiPost(`/api/alerts/${a.alert_id}/review`, { action });
      toast.success(
        action === "verify"
          ? `Signal verified. ${a.facility_ids.length} facilities notified.`
          : "Signal dismissed.",
      );
      onChanged();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {surges.length === 0 && <p className="text-sm text-muted-foreground">No possible surge signals in this district.</p>}
      {surges.map((a) => {
        const reviewed = a.review?.status ?? (a.status !== "pending_review" ? a.status : null);
        return (
          <div
            key={a.alert_id}
            className={cn(
              "rounded-lg border p-3",
              reviewed === "dismissed" ? "opacity-70" : "border-red-300 bg-red-50/50 dark:border-red-900 dark:bg-red-950/20",
            )}
          >
            <div className="flex flex-wrap items-center gap-2">
              <AlertTriangle className="size-4 text-red-600" />
              <span className="font-semibold">{a.context.label ?? "Possible surge"}</span>
              {a.context.ratio != null && (
                <span className="rounded bg-red-600 px-1.5 py-0.5 text-[11px] font-semibold text-white">
                  {a.context.ratio.toFixed(1)}× normal
                </span>
              )}
              <span className="text-xs text-muted-foreground">{a.severity} severity</span>
            </div>
            <p className="mt-1 text-sm">{a.summary}</p>
            <div className="mt-1 text-xs text-muted-foreground">
              Blocks: {(a.context.blocks ?? []).join(", ") || "–"} · {a.facility_ids.length} facilities · medicines:{" "}
              {a.drug_codes.join(", ")}
            </div>
            <p className="mt-1.5 rounded bg-amber-100 px-2 py-1 text-xs font-medium text-amber-900 dark:bg-amber-900/40 dark:text-amber-100">
              Possible signal — verify. Possible signals for verification, not confirmed outbreaks.
            </p>
            {reviewed ? (
              <p className="mt-2 text-xs">
                <span className={cn("font-semibold", reviewed === "verified" ? "text-emerald-700 dark:text-emerald-400" : "text-muted-foreground")}>
                  {reviewed === "verified" ? "Verified · facilities notified" : "Dismissed"}
                </span>
                {a.review && (
                  <span className="text-muted-foreground">
                    {" "}
                    by {a.review.by} · {fmtDate(a.review.at)}
                  </span>
                )}
              </p>
            ) : (
              <div className="mt-2 flex flex-wrap gap-2">
                <Button size="sm" disabled={busy === a.alert_id} onClick={() => review(a, "verify")}>
                  Verify &amp; notify facilities
                </Button>
                <Button size="sm" variant="outline" disabled={busy === a.alert_id} onClick={() => review(a, "dismiss")}>
                  Dismiss
                </Button>
              </div>
            )}
          </div>
        );
      })}

      {facilityAlerts.length > 0 && (
        <div>
          <div className="mb-1 text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Stock-out alerts ({facilityAlerts.length})
          </div>
          <ul className="max-h-64 divide-y overflow-y-auto rounded-lg border">
            {facilityAlerts.map((a) => {
              const fid = a.facility_ids[0];
              return (
                <li key={a.alert_id}>
                  <button
                    type="button"
                    className="flex w-full items-start gap-2 px-2.5 py-1.5 text-left text-sm hover:bg-muted"
                    onClick={() => fid && onSelectFacility(fid)}
                  >
                    <span
                      className={cn(
                        "mt-1 inline-block size-2 shrink-0 rounded-full",
                        a.type === "stocked_out" ? "bg-red-600" : "bg-orange-500",
                      )}
                    />
                    <span className="min-w-0">
                      <span className="font-medium">{a.context.facility_name ?? names.get(fid) ?? fid}</span>{" "}
                      <span className="text-xs text-muted-foreground">
                        {a.type === "stocked_out" ? "stocked out" : `risk ${fmtPct(a.context.max_risk)}`}
                      </span>
                      <span className="block truncate text-xs text-muted-foreground">{a.summary}</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
      {models.length > 0 && <p className="text-[11px] text-muted-foreground">Model: {models.join(", ")} · rule-based early warning</p>}
    </div>
  );
}
