import type { RiskBand, StockStatus } from "@/lib/types";

export const STATUS_CLASS: Record<StockStatus, string> = {
  adequate: "bg-emerald-100 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-100",
  low: "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100",
  critical: "bg-orange-200 text-orange-950 dark:bg-orange-900/50 dark:text-orange-100",
  stocked_out: "bg-red-600 text-white",
};

export const RISK_CLASS: Record<RiskBand, string> = {
  low: "text-emerald-700 dark:text-emerald-400",
  medium: "text-amber-700 dark:text-amber-400",
  high: "text-red-700 dark:text-red-400 font-semibold",
  stocked_out: "text-red-700 dark:text-red-400 font-semibold",
};

/** Readiness colour: Good >= 75, Moderate >= 50, Poor < 50. */
export function readinessColor(score: number | null | undefined): string {
  if (score == null) return "#64748b";
  if (score >= 75) return "#059669";
  if (score >= 50) return "#d97706";
  return "#dc2626";
}

export function fmtNum(n: number | null | undefined, digits = 0): string {
  if (n == null) return "–";
  return n.toLocaleString("en-IN", { maximumFractionDigits: digits });
}

export function fmtPct(n: number | null | undefined): string {
  return n == null ? "–" : `${Math.round(n * 100)}%`;
}

export function fmtAgo(hours: number | null | undefined): string {
  if (hours == null) return "never";
  if (hours < 1) return `${Math.max(1, Math.round(hours * 60))} min ago`;
  if (hours < 48) return `${Math.round(hours)} h ago`;
  return `${Math.round(hours / 24)} days ago`;
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "–";
  return new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
}
