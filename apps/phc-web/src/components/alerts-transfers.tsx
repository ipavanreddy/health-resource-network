"use client";

import { toast } from "sonner";
import { Volume2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { speak } from "@/components/report-stock";
import { apiPost } from "@/lib/api";
import { fmtDate, fmtNum } from "@/lib/format";
import { t, type Lang } from "@/lib/i18n";
import type { Alert, Notification, Transfer } from "@/lib/types";

const STATUS_PILL: Record<Transfer["status"], string> = {
  proposed: "bg-amber-100 text-amber-900",
  approved: "bg-blue-100 text-blue-900",
  dispatched: "bg-indigo-100 text-indigo-900",
  received: "bg-emerald-100 text-emerald-900",
  rejected: "bg-muted text-muted-foreground",
};

export function AlertsList({ alerts, lang }: { alerts: Alert[]; lang: Lang }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("alerts", lang)}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {alerts.length === 0 && <p className="text-sm text-muted-foreground">{t("noAlerts", lang)}</p>}
        {alerts.map((a) => (
          <div
            key={a.alert_id}
            className={`rounded-md border p-3 text-sm ${a.severity === "high" ? "border-red-300 bg-red-50 dark:bg-red-950/40" : "border-amber-300 bg-amber-50 dark:bg-amber-950/40"}`}
          >
            <div className="flex items-start justify-between gap-2">
              <p>{a.summary}</p>
              <Button size="icon-sm" variant="ghost" aria-label={t("play", lang)} onClick={() => speak(a.summary, lang)}>
                <Volume2 />
              </Button>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {a.type === "surge" ? "Verified by District Health Officer · " : ""}
              {a.model_name} {a.model_version}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function TransfersList({
  transfers,
  facilityId,
  lang,
  onChanged,
}: {
  transfers: Transfer[];
  facilityId: string;
  lang: Lang;
  onChanged: () => void;
}) {
  async function act(id: string, action: "dispatch" | "receive") {
    try {
      await apiPost(`/api/transfers/${id}/${action}`, { by: "PHC staff" });
      toast.success(action === "receive" ? "Receipt confirmed. Stock updated." : "Marked dispatched");
      onChanged();
    } catch (e) {
      toast.error(String(e));
    }
  }
  const visible = transfers.filter((tr) => tr.status !== "rejected");
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("transfers", lang)}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {visible.length === 0 && <p className="text-sm text-muted-foreground">{t("noTransfers", lang)}</p>}
        {visible.map((tr) => {
          const incoming = tr.to_facility_id === facilityId;
          return (
            <div key={tr.transfer_id} className="rounded-md border p-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{incoming ? t("incoming", lang) : t("outgoing", lang)}</Badge>
                <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_PILL[tr.status]}`}>{tr.status}</span>
                <span className="font-medium">
                  {fmtNum(tr.quantity)} {tr.unit}s · {tr.medicine}
                </span>
              </div>
              <p className="mt-1 text-muted-foreground">
                {tr.from_name} → {tr.to_name} · ~{Math.round(tr.travel_minutes)} min
              </p>
              {tr.status !== "proposed" && <p className="mt-1 text-xs">{tr.explanation.transfer_note}</p>}
              <p className="mt-1 text-xs text-muted-foreground">
                {tr.history.map((h) => `${h.status} ${fmtDate(h.at)}`).join(" → ")}
              </p>
              <div className="mt-2 flex gap-2">
                {!incoming && tr.status === "approved" && (
                  <Button size="lg" onClick={() => act(tr.transfer_id, "dispatch")}>
                    {t("markDispatched", lang)}
                  </Button>
                )}
                {incoming && tr.status === "dispatched" && (
                  <Button size="lg" onClick={() => act(tr.transfer_id, "receive")}>
                    {t("confirmReceipt", lang)}
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

export function NotificationsList({ notifications, lang }: { notifications: Notification[]; lang: Lang }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("notifications", lang)}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {notifications.length === 0 && <p className="text-muted-foreground">{t("noNotifications", lang)}</p>}
        {notifications.map((n) => (
          <div key={n.notification_id} className="flex items-start justify-between gap-2 border-b pb-2 last:border-0">
            <div>
              <p>{n.texts[lang] ?? n.texts.en}</p>
              <p className="text-xs text-muted-foreground">
                {fmtDate(n.created_at)} · {n.channel === "firestore" ? "Firestore" : "in-app (demo)"}
              </p>
            </div>
            <Button size="icon-sm" variant="ghost" aria-label={t("play", lang)} onClick={() => speak(n.texts[lang] ?? n.texts.en, lang)}>
              <Volume2 />
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
