import { cn } from "@/lib/utils";
import { STATUS_CLASS, readinessColor } from "@/lib/format";
import type { StockStatus, Transfer } from "@/lib/types";

export function StatusPill({ status, className }: { status: StockStatus | undefined; className?: string }) {
  if (!status) return <span className="text-muted-foreground">–</span>;
  return (
    <span className={cn("inline-flex rounded px-1.5 py-0.5 text-[11px] font-medium whitespace-nowrap", STATUS_CLASS[status], className)}>
      {status.replace("_", " ")}
    </span>
  );
}

const TRANSFER_CLASS: Record<Transfer["status"], string> = {
  proposed: "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100",
  approved: "bg-blue-100 text-blue-900 dark:bg-blue-900/40 dark:text-blue-100",
  dispatched: "bg-indigo-100 text-indigo-900 dark:bg-indigo-900/40 dark:text-indigo-100",
  received: "bg-emerald-100 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-100",
  rejected: "bg-muted text-muted-foreground line-through",
};

export function TransferPill({ status }: { status: Transfer["status"] }) {
  return (
    <span className={cn("inline-flex rounded px-1.5 py-0.5 text-[11px] font-medium uppercase tracking-wide", TRANSFER_CLASS[status])}>
      {status}
    </span>
  );
}

export function ReadinessChip({ score, band }: { score: number | null | undefined; band?: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
      <span className="inline-block size-2.5 rounded-full" style={{ background: readinessColor(score) }} />
      <span className="font-semibold tabular-nums">{score ?? "–"}</span>
      {band && <span className="text-xs text-muted-foreground">{band}</span>}
    </span>
  );
}

export function SyntheticNote({ className }: { className?: string }) {
  return (
    <p className={cn("text-[11px] text-amber-800 dark:text-amber-300", className)}>
      Synthetic data: generated for demonstration; not real facility, stock or patient data.
    </p>
  );
}
