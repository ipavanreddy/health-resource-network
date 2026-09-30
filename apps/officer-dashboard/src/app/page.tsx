"use client";

import { useCallback, useMemo, useState, type ReactNode } from "react";
import { Activity } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ModeBanner } from "@/components/mode-banner";
import { KpiRow } from "@/components/kpi-row";
import { MAPS_FALLBACK, MapPanel } from "@/components/map-panel";
import { AlertsPanel } from "@/components/alerts-panel";
import { TransferPanel } from "@/components/transfer-panel";
import { FacilityTable } from "@/components/facility-table";
import { FacilityDetailPanel } from "@/components/facility-detail";
import { InteropPanel } from "@/components/interop-panel";
import { ScenarioPanel } from "@/components/scenario-panel";
import { SyntheticNote } from "@/components/bits";
import { setRole } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { cn } from "@/lib/utils";
import type { Alert, FacilitySummary, Medicine, Notification, Overview, StateConfig, Transfer } from "@/lib/types";

setRole("district_health_officer");

const selectCls =
  "h-8 min-w-0 rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/50 disabled:opacity-50";

function Section({ title, aside, children, className }: { title: string; aside?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={cn("flex min-w-0 flex-col gap-3 rounded-xl border bg-card p-3 sm:p-4", className)}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold">{title}</h2>
        {aside}
      </div>
      {children}
    </section>
  );
}

export default function DhoDashboard() {
  const [stateId, setStateId] = useState("TN");
  const [district, setDistrict] = useState("MDU");
  const [selected, setSelected] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  const scope = `state=${stateId}&district=${district}`;
  const states = useApi<{ states: StateConfig[] }>("/api/states");
  const medicines = useApi<{ medicines: Medicine[] }>("/api/medicines");
  const overview = useApi<Overview>(`/api/overview?${scope}`, version);
  const facilities = useApi<{ facilities: FacilitySummary[] }>(`/api/facilities?${scope}`, version);
  const alerts = useApi<{ alerts: Alert[] }>(`/api/alerts?${scope}`, version);
  const transfers = useApi<{ transfers: Transfer[] }>(`/api/transfers?${scope}`, version);
  const notifications = useApi<{ notifications: Notification[] }>(`/api/districts/${district}/notifications`, version);

  const stateList = useMemo(() => states.data?.states ?? [], [states.data]);
  const stateConfig = stateList.find((s) => s.id === stateId);
  const scenario = stateConfig?.scenarios.find((s) => s.district === district);
  const facilityList = useMemo(() => facilities.data?.facilities ?? [], [facilities.data]);
  const transferList = useMemo(() => transfers.data?.transfers ?? [], [transfers.data]);
  const medicineList = useMemo(() => medicines.data?.medicines ?? [], [medicines.data]);
  const drugNames = useMemo(() => new Map(medicineList.map((m) => [m.drug_code, m.name])), [medicineList]);
  const surgeFacilityIds = useMemo(
    () =>
      (alerts.data?.alerts ?? [])
        .filter((a) => a.type === "surge" && a.review?.status !== "dismissed" && a.status !== "dismissed")
        .flatMap((a) => a.facility_ids),
    [alerts.data],
  );

  const refresh = useCallback(() => setVersion((v) => v + 1), []);
  const select = useCallback((id: string) => setSelected(id), []);
  const closeDetail = useCallback(() => setSelected(null), []);

  function changeState(id: string) {
    const cfg = stateList.find((s) => s.id === id);
    setStateId(id);
    setDistrict(cfg?.scenarios[0]?.district ?? cfg?.districts[0]?.id ?? "");
    setSelected(null);
  }

  const apiError = overview.error ?? facilities.error ?? states.error;

  return (
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-4 px-3 py-3 sm:px-5 sm:py-4">
      <header className="flex flex-col gap-2">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2">
            <Activity className="size-6 shrink-0 text-primary" />
            <div className="min-w-0">
              <h1 className="text-lg leading-tight font-semibold sm:text-xl">PHC Pulse · District Health Officer</h1>
              <p className="text-xs text-muted-foreground">Medicine availability, early warnings and redistribution for your district</p>
            </div>
          </div>
          <ModeBanner extraDemo={MAPS_FALLBACK ? "Map: OpenStreetMap/Leaflet fallback (set NEXT_PUBLIC_MAPS_API_KEY for Google Maps)" : undefined} />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
            State
            <select className={selectCls} value={stateId} onChange={(e) => changeState(e.target.value)} disabled={!stateList.length}>
              {stateList.length === 0 && <option value={stateId}>{stateId}</option>}
              {stateList.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
            District
            <select
              className={selectCls}
              value={district}
              onChange={(e) => {
                setDistrict(e.target.value);
                setSelected(null);
              }}
              disabled={!stateConfig}
            >
              {!stateConfig && <option value={district}>{district}</option>}
              {stateConfig?.districts.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>
          {stateConfig && (
            <span className="text-xs text-muted-foreground">
              Season focus: <span className="font-medium text-foreground">{stateConfig.season_focus}</span>
              {scenario && <span className="hidden md:inline"> · Demo scenario {scenario.id}: {scenario.title}</span>}
            </span>
          )}
        </div>
        {apiError && (
          <p className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            Could not load data from the API: {apiError}
          </p>
        )}
      </header>

      <KpiRow overview={overview.data} />

      <Tabs defaultValue="ops">
        <TabsList>
          <TabsTrigger value="ops">Operations</TabsTrigger>
          <TabsTrigger value="interop">Interoperability &amp; models</TabsTrigger>
        </TabsList>

        <TabsContent value="ops" className="flex flex-col gap-4 pt-2">
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
            <div className="flex min-w-0 flex-col gap-4">
              <Section title="Facility map" aside={<span className="text-xs text-muted-foreground">Click a facility for details</span>}>
                <MapPanel
                  facilities={facilityList}
                  transfers={transferList}
                  surgeFacilityIds={surgeFacilityIds}
                  selectedId={selected}
                  onSelect={select}
                  scopeKey={`${stateId}/${district}`}
                />
              </Section>
              <Section title="Early warnings" aside={<span className="text-xs text-muted-foreground">Possible signals for verification, not confirmed outbreaks</span>}>
                <AlertsPanel alerts={alerts.data?.alerts} facilities={facilityList} onSelectFacility={select} onChanged={refresh} />
              </Section>
            </div>
            <Section title="Transfer review" aside={<span className="text-xs text-muted-foreground">Optimiser proposes · DHO decides</span>}>
              <TransferPanel
                key={`${stateId}/${district}`}
                state={stateId}
                district={district}
                stateConfig={stateConfig}
                transfers={transfers.data?.transfers}
                medicines={medicineList}
                notifications={notifications.data?.notifications}
                onChanged={refresh}
                onSelectFacility={select}
              />
            </Section>
          </div>
          <Section title="Facilities" aside={<span className="text-xs text-muted-foreground">Sorted by readiness (lowest first) · click a row for details</span>}>
            <FacilityTable facilities={facilities.data?.facilities} selectedId={selected} onSelect={select} drugNames={drugNames} />
            <SyntheticNote />
          </Section>
          <Section title="Emergency scenario" aside={<span className="text-xs text-muted-foreground">Apply an outbreak multiplier · projected stock-outs by week</span>}>
            <ScenarioPanel key={`${stateId}/${district}`} state={stateId} district={district} medicines={medicineList} defaultGroup={scenario?.group} />
          </Section>
        </TabsContent>

        <TabsContent value="interop" className="pt-2">
          {stateList.length > 0 ? <InteropPanel states={stateList} stateId={stateId} /> : <p className="text-sm text-muted-foreground">Loading states…</p>}
        </TabsContent>
      </Tabs>

      {selected && <FacilityDetailPanel key={selected} facilityId={selected} version={version} onClose={closeDetail} />}
    </div>
  );
}
