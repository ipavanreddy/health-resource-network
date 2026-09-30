"use client";

import { useEffect, useState } from "react";
import { Bell, ClipboardList, Mic } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertsList, NotificationsList, TransfersList } from "@/components/alerts-transfers";
import { ModeBanner } from "@/components/mode-banner";
import { ReportStock } from "@/components/report-stock";
import { BedsStaffCard, ReadinessCard, StockTable } from "@/components/stock-view";
import { apiGet, setRole } from "@/lib/api";
import { readinessColor } from "@/lib/format";
import { LANGS, t, type Lang } from "@/lib/i18n";
import type { Alert, FacilityDetail, FacilitySummary, Notification, Readiness, Scenario, StockRow, Transfer } from "@/lib/types";

setRole("phc_staff");

interface Data {
  facility: FacilityDetail;
  stock: StockRow[];
  readiness: Readiness;
  alerts: Alert[];
  transfers: Transfer[];
  notifications: Notification[];
}

async function loadAll(fid: string, lang: Lang): Promise<Data> {
  const [facility, stock, readiness, alerts, transfers, notifications] = await Promise.all([
    apiGet<FacilityDetail>(`/api/facilities/${fid}`),
    apiGet<{ stock: StockRow[] }>(`/api/facilities/${fid}/stock`),
    apiGet<Readiness>(`/api/facilities/${fid}/readiness`),
    apiGet<{ alerts: Alert[] }>(`/api/alerts?facility_id=${fid}&language=${lang}`),
    apiGet<{ transfers: Transfer[] }>(`/api/transfers?facility_id=${fid}`),
    apiGet<{ notifications: Notification[] }>(`/api/facilities/${fid}/notifications`),
  ]);
  return {
    facility,
    stock: stock.stock,
    readiness,
    alerts: alerts.alerts,
    transfers: transfers.transfers,
    notifications: notifications.notifications,
  };
}

export function PhcApp() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [scenarioId, setScenarioId] = useState("A");
  const [facilities, setFacilities] = useState<FacilitySummary[]>([]);
  const [facilityId, setFacilityId] = useState<string | null>(null);
  const [lang, setLang] = useState<Lang>("ta");
  const [tab, setTab] = useState("report");
  const [data, setData] = useState<Data | null>(null);
  const [version, setVersion] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const scenario = scenarios.find((s) => s.id === scenarioId);

  useEffect(() => {
    apiGet<{ scenarios: Scenario[] }>("/api/demo/scenarios")
      .then((r) => {
        setScenarios(r.scenarios);
        const a = r.scenarios[0];
        if (a) {
          setFacilityId(a.hero_facility_id);
          setLang(a.language as Lang);
        }
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!scenario) return;
    apiGet<{ facilities: FacilitySummary[] }>(
      `/api/facilities?state=${scenario.state}&district=${scenario.district}&include_warehouses=false`,
    )
      .then((r) => setFacilities(r.facilities))
      .catch((e) => setError(String(e)));
  }, [scenario]);

  useEffect(() => {
    if (!facilityId) return;
    let alive = true;
    loadAll(facilityId, lang)
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(String(e)));
    return () => {
      alive = false;
    };
  }, [facilityId, lang, version]);

  useEffect(() => {
    const id = setInterval(() => setVersion((v) => v + 1), 15000);
    return () => clearInterval(id);
  }, []);

  const refresh = () => setVersion((v) => v + 1);
  const pendingIncoming = data?.transfers.filter(
    (tr) => tr.to_facility_id === facilityId && tr.status === "dispatched",
  ).length;

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-4 p-4 sm:p-6">
      <header className="flex flex-col gap-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <Badge variant="secondary">{t("role", lang)}</Badge>
            <h1 className="text-2xl font-semibold tracking-tight">PHC Pulse</h1>
          </div>
          <ModeBanner />
        </div>
        <div className="grid gap-2 sm:grid-cols-3">
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            {t("scenario", lang)}
            <select
              className="h-10 rounded-lg border bg-background px-2 text-sm text-foreground"
              value={scenarioId}
              onChange={(e) => {
                const s = scenarios.find((x) => x.id === e.target.value);
                setScenarioId(e.target.value);
                if (s) {
                  setFacilityId(s.hero_facility_id);
                  setLang(s.language as Lang);
                  setData(null);
                }
              }}
            >
              {scenarios.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.id}. {s.title}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            {t("facility", lang)}
            <select
              className="h-10 rounded-lg border bg-background px-2 text-sm text-foreground"
              value={facilityId ?? ""}
              onChange={(e) => {
                setFacilityId(e.target.value);
                setData(null);
              }}
            >
              {facilities.map((f) => (
                <option key={f.facility_id} value={f.facility_id}>
                  {f.name} · {f.block} ({f.facility_id})
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            {t("language", lang)}
            <select
              className="h-10 rounded-lg border bg-background px-2 text-sm text-foreground"
              value={lang}
              onChange={(e) => setLang(e.target.value as Lang)}
            >
              {LANGS.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        {data && (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-lg border p-3 text-sm">
            <span className="text-lg font-semibold">{data.facility.name}</span>
            <span className="text-muted-foreground">
              {data.facility.block}, {data.facility.district_name} · {data.facility.type} · HFR {data.facility.hfr_id}
            </span>
            <span>
              {t("readiness", lang)}:{" "}
              <b style={{ color: readinessColor(data.readiness.score) }}>
                {data.readiness.score}/100 {data.readiness.band}
              </b>
            </span>
            {data.facility.warehouse && (
              <span className="text-xs text-muted-foreground">
                Warehouse: {data.facility.warehouse.name} · lead time {data.facility.lead_time_days} days
              </span>
            )}
          </div>
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}
      </header>

      <Tabs value={tab} onValueChange={(v) => setTab(String(v))}>
        <TabsList className="h-auto w-full flex-wrap">
          <TabsTrigger value="report" className="py-1.5">
            <Mic /> {t("tabReport", lang)}
          </TabsTrigger>
          <TabsTrigger value="stock" className="py-1.5">
            <ClipboardList /> {t("tabStock", lang)}
          </TabsTrigger>
          <TabsTrigger value="alerts" className="py-1.5">
            <Bell /> {t("tabAlerts", lang)}
            {(data?.alerts.length ?? 0) + (pendingIncoming ?? 0) > 0 && (
              <Badge variant="destructive">{(data?.alerts.length ?? 0) + (pendingIncoming ?? 0)}</Badge>
            )}
          </TabsTrigger>
        </TabsList>
        <TabsContent value="report" className="pt-2">
          {facilityId && data && (
            <ReportStock
              key={facilityId}
              facilityId={facilityId}
              lang={lang}
              stock={data.stock}
              onSaved={() => {
                refresh();
                setTab("stock");
              }}
            />
          )}
        </TabsContent>
        <TabsContent value="stock" className="space-y-4 pt-2">
          {data && (
            <>
              <StockTable stock={data.stock} lang={lang} />
              <div className="grid gap-4 md:grid-cols-2">
                <ReadinessCard readiness={data.readiness} lang={lang} />
                <BedsStaffCard key={`${facilityId}-${version}`} facility={data.facility} lang={lang} onChanged={refresh} />
              </div>
            </>
          )}
        </TabsContent>
        <TabsContent value="alerts" className="space-y-4 pt-2">
          {data && facilityId && (
            <>
              <AlertsList alerts={data.alerts} lang={lang} />
              <TransfersList transfers={data.transfers} facilityId={facilityId} lang={lang} onChanged={refresh} />
              <NotificationsList notifications={data.notifications} lang={lang} />
            </>
          )}
        </TabsContent>
      </Tabs>
      <footer className="text-xs text-muted-foreground">{t("synthetic", lang)}</footer>
    </main>
  );
}
