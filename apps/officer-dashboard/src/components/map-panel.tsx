"use client";

import dynamic from "next/dynamic";
import type { ReactNode } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import type { FacilityMapProps } from "@/components/facility-map";

// Leaflet / Google Maps touch `window`: client-only.
const FacilityMap = dynamic(() => import("@/components/facility-map"), {
  ssr: false,
  loading: () => <Skeleton className="h-full w-full" />,
});

export const MAPS_FALLBACK = !process.env.NEXT_PUBLIC_MAPS_API_KEY;

function Swatch({ children, label }: { children: ReactNode; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      {children}
      {label}
    </span>
  );
}

const dot = (color: string, size = 10) => (
  <span className="inline-block rounded-full border border-white" style={{ background: color, width: size, height: size }} />
);
const line = (color: string, dashed: boolean) => (
  <span className="inline-block w-5" style={{ borderTop: `3px ${dashed ? "dashed" : "solid"} ${color}` }} />
);

export function MapPanel(props: FacilityMapProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="relative isolate h-[320px] overflow-hidden rounded-lg border sm:h-[440px]">
        <FacilityMap {...props} />
        {MAPS_FALLBACK && (
          <span className="pointer-events-none absolute top-2 right-2 z-[500] rounded bg-background/90 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground shadow">
            Map: OpenStreetMap (demo fallback)
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
        <Swatch label="Readiness ≥75">{dot("#059669")}</Swatch>
        <Swatch label="50–74">{dot("#d97706")}</Swatch>
        <Swatch label="<50">{dot("#dc2626")}</Swatch>
        <Swatch label="Larger = stocked-out / high risk">{dot("#64748b", 14)}</Swatch>
        <Swatch label="District warehouse">
          <span className="inline-block size-2.5 bg-slate-800" />
        </Swatch>
        <Swatch label="Possible surge (to verify)">
          <span className="inline-block size-3.5 rounded-full border border-red-600 bg-red-500/20" />
        </Swatch>
        <Swatch label="Proposed">{line("#d97706", true)}</Swatch>
        <Swatch label="Approved / dispatched">{line("#2563eb", false)}</Swatch>
        <Swatch label="Received">{line("#059669", false)}</Swatch>
      </div>
    </div>
  );
}
