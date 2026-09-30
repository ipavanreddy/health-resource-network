"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";

interface Loaded<T> {
  path: string;
  version: number;
  data?: T;
  error?: string;
}

/**
 * GET `path` (null = skip). Bump `version` to refetch; previous data for the same path is kept while
 * refetching so the UI does not flicker. State is only set from promise callbacks (react-hooks v7).
 */
export function useApi<T>(path: string | null, version = 0) {
  const [loaded, setLoaded] = useState<Loaded<T> | null>(null);

  useEffect(() => {
    if (!path) return;
    let cancelled = false;
    apiGet<T>(path).then(
      (data) => {
        if (!cancelled) setLoaded({ path, version, data });
      },
      (e: unknown) => {
        if (!cancelled) setLoaded({ path, version, error: e instanceof Error ? e.message : String(e) });
      },
    );
    return () => {
      cancelled = true;
    };
  }, [path, version]);

  const samePath = loaded != null && loaded.path === path;
  return {
    data: samePath ? loaded.data : undefined,
    error: samePath ? loaded.error : undefined,
    loading: path != null && !(samePath && loaded.version === version),
  };
}
