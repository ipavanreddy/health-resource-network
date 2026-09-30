"use client";

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useEffect, useRef, useState } from "react";
import { fmtAgo, readinessColor } from "@/lib/format";
import type { FacilitySummary, Transfer } from "@/lib/types";

export interface FacilityMapProps {
  facilities: FacilitySummary[];
  transfers: Transfer[];
  surgeFacilityIds: string[];
  selectedId: string | null;
  onSelect: (facilityId: string) => void;
  /** Changes when state/district changes: the map re-fits its bounds once per scope. */
  scopeKey: string;
}

const MAPS_KEY = process.env.NEXT_PUBLIC_MAPS_API_KEY ?? "";

export const ROUTE_STYLE: Record<string, { color: string; dashed: boolean }> = {
  proposed: { color: "#d97706", dashed: true },
  approved: { color: "#2563eb", dashed: false },
  dispatched: { color: "#2563eb", dashed: false },
  received: { color: "#059669", dashed: false },
};

function esc(s: string): string {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] ?? c);
}

function isHighRisk(f: FacilitySummary): boolean {
  return f.worst_status === "stocked_out" || (f.stocked_out?.length ?? 0) > 0 || (f.high_risk?.length ?? 0) > 0;
}

function facilityPopup(f: FacilitySummary): string {
  if (f.is_warehouse) {
    return `<b>${esc(f.name)}</b><br/>District drug warehouse · ${esc(f.block)} block`;
  }
  const r = f.readiness;
  const risk = [...new Set([...(f.stocked_out ?? []), ...(f.high_risk ?? [])])];
  return [
    `<b>${esc(f.name)}</b> <span style="color:#64748b">${esc(f.type)} · ${esc(f.block)}</span>`,
    `Readiness: <b style="color:${readinessColor(r?.score)}">${r?.score ?? "–"}</b> ${esc(r?.band ?? "")}`,
    `Worst stock status: <b>${esc((f.worst_status ?? "–").replace("_", " "))}</b>`,
    risk.length ? `High risk / out: ${esc(risk.join(", "))}` : "",
    f.surge_groups?.length ? `<span style="color:#b91c1c">Possible surge: ${esc(f.surge_groups.join(", "))}</span>` : "",
    `Last report: ${esc(fmtAgo(f.freshness_hours))}${f.stale ? ' <b style="color:#dc2626">STALE</b>' : ""}`,
    `<i style="color:#64748b">Click marker to open details</i>`,
  ]
    .filter(Boolean)
    .join("<br/>");
}

function transferPopup(t: Transfer): string {
  return [
    `<b>${esc(t.status.toUpperCase())}</b>: ${t.quantity.toLocaleString("en-IN")} ${esc(t.unit)}s ${esc(t.medicine)}`,
    `${esc(t.from_name)} → ${esc(t.to_name)}`,
    `~${Math.round(t.travel_minutes)} min${t.travel_mode === "haversine" ? " (straight-line estimate)" : ""}`,
  ].join("<br/>");
}

function routable(transfers: Transfer[]): Transfer[] {
  return transfers.filter((t) => t.status in ROUTE_STYLE);
}

export default function FacilityMap(props: FacilityMapProps) {
  return MAPS_KEY ? <GoogleFacilityMap {...props} /> : <LeafletFacilityMap {...props} />;
}

// ------------------------------------------------------------------------------------------ Leaflet

function LeafletFacilityMap({ facilities, transfers, surgeFacilityIds, selectedId, onSelect, scopeKey }: FacilityMapProps) {
  const elRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);
  const fittedRef = useRef<string | null>(null);
  const onSelectRef = useRef(onSelect);

  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    if (!elRef.current) return;
    const map = L.map(elRef.current, { scrollWheelZoom: false }).setView([20.5, 79], 5);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
      maxZoom: 18,
    }).addTo(map);
    mapRef.current = map;
    layerRef.current = L.layerGroup().addTo(map);
    // Container can be laid out after init (dynamic import, tabs, iframes): keep Leaflet's size in sync.
    const ro = new ResizeObserver(() => map.invalidateSize());
    ro.observe(elRef.current);
    return () => {
      ro.disconnect();
      map.remove();
      mapRef.current = null;
      layerRef.current = null;
      fittedRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer) return;
    layer.clearLayers();
    const surge = new Set(surgeFacilityIds);

    for (const f of facilities) {
      if (surge.has(f.facility_id)) {
        L.circleMarker([f.lat, f.lng], {
          radius: 20,
          color: "#dc2626",
          weight: 1,
          fillColor: "#ef4444",
          fillOpacity: 0.15,
          interactive: false,
        }).addTo(layer);
      }
    }

    for (const t of routable(transfers)) {
      const st = ROUTE_STYLE[t.status];
      L.polyline(
        [
          [t.from_location.lat, t.from_location.lng],
          [t.to_location.lat, t.to_location.lng],
        ],
        { color: st.color, weight: 3, opacity: 0.9, dashArray: st.dashed ? "6 6" : undefined },
      )
        .bindPopup(transferPopup(t))
        .addTo(layer);
      // receiver end-point dot
      L.circleMarker([t.to_location.lat, t.to_location.lng], { radius: 3, color: st.color, fillOpacity: 1, interactive: false }).addTo(layer);
    }

    for (const f of facilities) {
      const selected = f.facility_id === selectedId;
      let marker: L.Layer;
      if (f.is_warehouse) {
        marker = L.marker([f.lat, f.lng], {
          icon: L.divIcon({
            className: "",
            html: '<div style="width:14px;height:14px;background:#1e293b;border:2px solid #fff;box-shadow:0 0 0 1px #1e293b"></div>',
            iconSize: [14, 14],
            iconAnchor: [7, 7],
          }),
          title: f.name,
        });
      } else {
        marker = L.circleMarker([f.lat, f.lng], {
          radius: isHighRisk(f) ? 10 : 7,
          color: selected ? "#0f172a" : "#ffffff",
          weight: selected ? 3 : 1.5,
          fillColor: readinessColor(f.readiness?.score),
          fillOpacity: 0.95,
        });
      }
      marker.bindPopup(facilityPopup(f));
      if (!f.is_warehouse) marker.on("click", () => onSelectRef.current(f.facility_id));
      marker.addTo(layer);
    }

    if (facilities.length > 0 && fittedRef.current !== scopeKey) {
      const bounds = L.latLngBounds(facilities.map((f) => [f.lat, f.lng] as [number, number]));
      map.fitBounds(bounds, { padding: [24, 24], maxZoom: 12 });
      fittedRef.current = scopeKey;
    }
  }, [facilities, transfers, surgeFacilityIds, selectedId, scopeKey]);

  return <div ref={elRef} className="h-full w-full" aria-label="Facility map" />;
}

// ------------------------------------------------------------------------------------ Google Maps

interface GLatLng {
  lat: number;
  lng: number;
}
interface GOverlay {
  setMap(map: GMap | null): void;
  addListener(event: string, fn: () => void): void;
}
interface GMap {
  fitBounds(bounds: GBounds, padding?: number): void;
}
interface GBounds {
  extend(p: GLatLng): void;
}
interface GInfoWindow {
  setContent(content: string): void;
  setPosition(p: GLatLng): void;
  open(opts: { map: GMap }): void;
}
interface GoogleMapsNS {
  Map: new (el: HTMLElement, opts: Record<string, unknown>) => GMap;
  Circle: new (opts: Record<string, unknown>) => GOverlay;
  Marker: new (opts: Record<string, unknown>) => GOverlay;
  Polyline: new (opts: Record<string, unknown>) => GOverlay;
  InfoWindow: new () => GInfoWindow;
  LatLngBounds: new () => GBounds;
  SymbolPath: { CIRCLE: number };
}
declare global {
  interface Window {
    google?: { maps: GoogleMapsNS };
  }
}

let gmapsPromise: Promise<GoogleMapsNS> | null = null;
function loadGoogleMaps(): Promise<GoogleMapsNS> {
  if (window.google?.maps) return Promise.resolve(window.google.maps);
  if (!gmapsPromise) {
    gmapsPromise = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(MAPS_KEY)}`;
      s.async = true;
      s.onload = () => (window.google?.maps ? resolve(window.google.maps) : reject(new Error("Google Maps failed to load")));
      s.onerror = () => {
        gmapsPromise = null;
        reject(new Error("Google Maps script failed to load"));
      };
      document.head.appendChild(s);
    });
  }
  return gmapsPromise;
}

function GoogleFacilityMap({ facilities, transfers, surgeFacilityIds, selectedId, onSelect, scopeKey }: FacilityMapProps) {
  const elRef = useRef<HTMLDivElement>(null);
  const [api, setApi] = useState<{ g: GoogleMapsNS; map: GMap; info: GInfoWindow } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fittedRef = useRef<string | null>(null);
  const onSelectRef = useRef(onSelect);

  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    let cancelled = false;
    loadGoogleMaps().then(
      (g) => {
        if (cancelled || !elRef.current) return;
        const map = new g.Map(elRef.current, { center: { lat: 20.5, lng: 79 }, zoom: 5, streetViewControl: false, mapTypeControl: false });
        setApi({ g, map, info: new g.InfoWindow() });
      },
      (e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      },
    );
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!api) return;
    const { g, map, info } = api;
    const overlays: GOverlay[] = [];
    const add = (o: GOverlay) => {
      overlays.push(o);
      return o;
    };
    const popup = (o: GOverlay, pos: GLatLng, html: string, after?: () => void) =>
      o.addListener("click", () => {
        info.setContent(html);
        info.setPosition(pos);
        info.open({ map });
        after?.();
      });
    const surge = new Set(surgeFacilityIds);

    for (const f of facilities) {
      if (surge.has(f.facility_id)) {
        add(new g.Circle({ map, center: { lat: f.lat, lng: f.lng }, radius: 2500, strokeColor: "#dc2626", strokeWeight: 1, fillColor: "#ef4444", fillOpacity: 0.15, clickable: false }));
      }
    }
    for (const t of routable(transfers)) {
      const st = ROUTE_STYLE[t.status];
      const path = [t.from_location, t.to_location];
      const line = add(
        new g.Polyline(
          st.dashed
            ? { map, path, strokeOpacity: 0, icons: [{ icon: { path: "M 0,-1 0,1", strokeOpacity: 1, strokeColor: st.color, scale: 3 }, offset: "0", repeat: "12px" }] }
            : { map, path, strokeColor: st.color, strokeWeight: 3, strokeOpacity: 0.9 },
        ),
      );
      popup(line, t.to_location, transferPopup(t));
    }
    for (const f of facilities) {
      const pos = { lat: f.lat, lng: f.lng };
      const selected = f.facility_id === selectedId;
      const icon = f.is_warehouse
        ? { path: "M -1,-1 1,-1 1,1 -1,1 z", scale: 7, fillColor: "#1e293b", fillOpacity: 1, strokeColor: "#ffffff", strokeWeight: 2 }
        : {
            path: g.SymbolPath.CIRCLE,
            scale: isHighRisk(f) ? 10 : 7,
            fillColor: readinessColor(f.readiness?.score),
            fillOpacity: 0.95,
            strokeColor: selected ? "#0f172a" : "#ffffff",
            strokeWeight: selected ? 3 : 1.5,
          };
      const m = add(new g.Marker({ map, position: pos, icon, title: f.name }));
      popup(m, pos, facilityPopup(f), f.is_warehouse ? undefined : () => onSelectRef.current(f.facility_id));
    }
    if (facilities.length > 0 && fittedRef.current !== scopeKey) {
      const b = new g.LatLngBounds();
      facilities.forEach((f) => b.extend({ lat: f.lat, lng: f.lng }));
      map.fitBounds(b, 24);
      fittedRef.current = scopeKey;
    }
    return () => overlays.forEach((o) => o.setMap(null));
  }, [api, facilities, transfers, surgeFacilityIds, selectedId, scopeKey]);

  return (
    <div className="relative h-full w-full">
      <div ref={elRef} className="h-full w-full" aria-label="Facility map" />
      {error && (
        <div className="absolute inset-0 grid place-items-center bg-background/80 p-4 text-center text-sm text-destructive">
          {error}. Unset NEXT_PUBLIC_MAPS_API_KEY to use the OpenStreetMap fallback.
        </div>
      )}
    </div>
  );
}
