"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiPost } from "@/lib/api";
import { fmtAgo, fmtNum, fmtPct, readinessColor, RISK_CLASS, STATUS_CLASS } from "@/lib/format";
import { t, type Lang } from "@/lib/i18n";
import type { FacilityDetail, Readiness, StockRow } from "@/lib/types";

export function ReadinessCard({ readiness, lang }: { readiness: Readiness; lang: Lang }) {
  const color = readinessColor(readiness.score);
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("readiness", lang)}</CardTitle>
        <CardDescription>{readiness.method}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex shrink-0 flex-col items-center">
          <span className="text-5xl font-semibold tabular-nums" style={{ color }}>
            {readiness.score}
          </span>
          <span className="text-sm text-muted-foreground">/ 100 · {readiness.band}</span>
        </div>
        <ul className="w-full space-y-2 text-sm">
          {readiness.components.map((c) => (
            <li key={c.key}>
              <div className="flex justify-between gap-2">
                <span>
                  {c.label} <span className="text-xs text-muted-foreground">({c.weight}%)</span>
                </span>
                <span className="tabular-nums">{c.points.toFixed(1)}</span>
              </div>
              <div className="h-1.5 rounded-full bg-muted" aria-hidden>
                <div className="h-1.5 rounded-full" style={{ width: `${c.score}%`, background: readinessColor(c.score) }} />
              </div>
              <div className="text-xs text-muted-foreground">{c.detail}</div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

export function StockTable({ stock, lang }: { stock: StockRow[]; lang: Lang }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("daysCover", lang)}</CardTitle>
        <CardDescription>{t("synthetic", lang)}</CardDescription>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead className="text-xs text-muted-foreground">
            <tr className="text-left">
              <th className="py-1 pr-2">{t("medicine", lang)}</th>
              <th className="pr-2 text-right">{t("onHand", lang)}</th>
              <th className="pr-2 text-right">{t("dailyUse", lang)}</th>
              <th className="pr-2 text-right">{t("daysCover", lang)}</th>
              <th className="pr-2">{t("status", lang)}</th>
              <th className="pr-2 text-right">{t("risk", lang)}</th>
              <th className="text-right">{t("forecastWeek", lang)}</th>
            </tr>
          </thead>
          <tbody>
            {stock.map((r) => (
              <tr key={r.drug_code} className="border-t align-top">
                <td className="py-1.5 pr-2">
                  <span className="font-medium">
                    {r.name} {r.strength}
                  </span>
                  {r.surge && <Badge className="ml-1 bg-orange-100 text-orange-900">{t("surge", lang)} ×{r.surge_ratio}</Badge>}
                  <div className="text-xs text-muted-foreground">
                    {r.source} · {fmtAgo(r.hours_since_update)}
                    {r.in_transit > 0 && ` · +${fmtNum(r.in_transit)} in transit`}
                    {r.near_expiry_qty > 0 && ` · ${fmtNum(r.near_expiry_qty)} near expiry`}
                  </div>
                </td>
                <td className="pr-2 text-right tabular-nums">{fmtNum(r.on_hand)}</td>
                <td className="pr-2 text-right tabular-nums">{fmtNum(r.daily_demand, 1)}</td>
                <td className="pr-2 text-right font-semibold tabular-nums">
                  {r.days_of_cover == null ? "–" : fmtNum(r.days_of_cover, 1)}
                </td>
                <td className="pr-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_CLASS[r.status]}`}>{t(r.status, lang)}</span>
                </td>
                <td className={`pr-2 text-right tabular-nums ${RISK_CLASS[r.risk_band]}`}>{fmtPct(r.stockout_risk)}</td>
                <td className="text-right tabular-nums">{fmtNum(r.forecast_next_week)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-2 text-xs text-muted-foreground">
          Days of cover = (on hand + in transit) ÷ average daily use over the last 7 days without stock-out. Risk = chance
          demand before the next supply (lead time) exceeds available stock.
        </p>
      </CardContent>
    </Card>
  );
}

export function BedsStaffCard({
  facility,
  lang,
  onChanged,
}: {
  facility: FacilityDetail;
  lang: Lang;
  onChanged: () => void;
}) {
  const beds = facility.beds ?? { total: 0, occupied: 0 };
  const staff = facility.staff ?? { sanctioned: 0, present: 0 };
  const [occupied, setOccupied] = useState(String(beds.occupied));
  const [busy, setBusy] = useState(false);

  async function saveBeds() {
    setBusy(true);
    try {
      await apiPost(`/api/facilities/${facility.facility_id}/beds`, { occupied: Number(occupied) });
      toast.success("Beds updated");
      onChanged();
    } catch (e) {
      toast.error(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function checkIn(simulate: boolean) {
    const post = async (lat: number, lng: number) => {
      const res = await apiPost<{ accepted: boolean; distance_m: number; geofence_m: number }>(
        `/api/facilities/${facility.facility_id}/attendance`,
        { lat, lng, token: `device-${Math.random().toString(36).slice(2, 10)}` },
      );
      if (res.accepted) toast.success(`Checked in (${res.distance_m} m from facility)`);
      else toast.error(`Outside the ${res.geofence_m} m geo-fence (${res.distance_m} m away)`);
      onChanged();
    };
    if (simulate || !("geolocation" in navigator)) return post(facility.lat, facility.lng);
    navigator.geolocation.getCurrentPosition(
      (p) => void post(p.coords.latitude, p.coords.longitude),
      () => toast.error("Location unavailable"),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {t("beds", lang)} & {t("staff", lang)}
        </CardTitle>
        {facility.freshness && (
          <CardDescription>
            {t("lastReport", lang)}: {fmtAgo(facility.freshness.stock.hours_ago)} ({facility.freshness.stock.source})
            {facility.freshness.stale && <Badge variant="destructive" className="ml-1">stale</Badge>}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div className="space-y-2">
          <div>
            <span className="text-2xl font-semibold tabular-nums">{beds.total - beds.occupied}</span> / {beds.total}{" "}
            {t("available", lang)}
          </div>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              min={0}
              max={beds.total}
              className="h-9 w-24"
              value={occupied}
              aria-label={t("occupied", lang)}
              onChange={(e) => setOccupied(e.target.value)}
            />
            <span className="text-muted-foreground">{t("occupied", lang)}</span>
            <Button onClick={saveBeds} disabled={busy} variant="outline" size="lg">
              {t("update", lang)}
            </Button>
          </div>
        </div>
        <div className="space-y-2">
          <div>
            <span className="text-2xl font-semibold tabular-nums">{staff.present}</span> / {staff.sanctioned}{" "}
            {t("staff", lang).toLowerCase()}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button size="lg" onClick={() => checkIn(false)}>
              {t("checkIn", lang)}
            </Button>
            <Button size="lg" variant="outline" onClick={() => checkIn(true)}>
              {t("checkInDemo", lang)}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">Only aggregate presence is shown; locations are not stored.</p>
        </div>
      </CardContent>
    </Card>
  );
}
