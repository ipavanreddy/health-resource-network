"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { apiGet } from "@/lib/api";
import type { SystemModes } from "@/lib/types";

/**
 * Always-visible labels: "Synthetic data" (all demo data is generated) and "Demo mode" whenever any
 * Google integration is running on its local fallback. Hover / tap for the per-integration list.
 */
export function ModeBanner({ extraDemo }: { extraDemo?: string }) {
  const [modes, setModes] = useState<SystemModes | null>(null);
  const [error, setError] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    apiGet<SystemModes>("/api/system/modes").then(setModes).catch(() => setError(true));
  }, []);

  if (error) return <Badge variant="destructive">API unreachable</Badge>;
  if (!modes) return <Badge variant="outline">Checking API…</Badge>;
  const demo = modes.integrations.filter((m) => m.mode === "demo");
  return (
    <div className="relative flex flex-wrap items-center gap-1.5">
      {modes.synthetic_data && (
        <Badge className="bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100" title={modes.notice}>
          Synthetic data
        </Badge>
      )}
      {(demo.length > 0 || extraDemo) && (
        <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
          <Badge className="cursor-pointer bg-violet-100 text-violet-900 dark:bg-violet-900/40 dark:text-violet-100">
            Demo mode · {demo.length}/{modes.integrations.length} fallbacks
          </Badge>
        </button>
      )}
      {demo.length === 0 && !extraDemo && <Badge variant="secondary">Live Google integrations</Badge>}
      {open && (
        <div className="absolute top-7 right-0 z-[1000] w-[min(92vw,26rem)] rounded-lg border bg-popover p-3 text-xs shadow-lg">
          <p className="mb-2 font-medium">Integration status</p>
          <ul className="space-y-1.5">
            {modes.integrations.map((m) => (
              <li key={m.id}>
                <span className={m.mode === "real" ? "text-emerald-700 dark:text-emerald-400" : "text-violet-700 dark:text-violet-300"}>
                  {m.mode === "real" ? "● live" : "○ demo"}
                </span>{" "}
                <span className="font-medium">{m.label}</span>
                {m.mode === "demo" && (
                  <div className="text-muted-foreground">
                    Fallback: {m.fallback}. Enable with <code>{m.enable_with}</code>.
                  </div>
                )}
              </li>
            ))}
            {extraDemo && <li className="text-muted-foreground">{extraDemo}</li>}
          </ul>
          <p className="mt-2 text-muted-foreground">{modes.notice}</p>
        </div>
      )}
    </div>
  );
}
