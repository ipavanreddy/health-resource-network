import { fmtNum } from "@/lib/format";
import type { Forecast } from "@/lib/types";

const W = 640;
const H = 220;
const PAD = { l: 44, r: 10, t: 12, b: 30 };

function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

/** Last 12 weeks of consumption (bars) + 8-week forecast (expected line, 80% low–high band). No chart library. */
export function ForecastChart({ forecast }: { forecast: Forecast }) {
  const hist = forecast.history.slice(-12);
  const fc = forecast.weeks;
  const n = hist.length + fc.length;
  if (n === 0) return <p className="text-xs text-muted-foreground">No forecast available.</p>;

  const max = Math.max(1, ...hist.map((h) => h.consumption), ...fc.map((w) => w.demand_high)) * 1.08;
  const plotW = W - PAD.l - PAD.r;
  const plotH = H - PAD.t - PAD.b;
  const slot = plotW / n;
  const x = (i: number) => PAD.l + slot * (i + 0.5);
  const y = (v: number) => PAD.t + plotH - (v / max) * plotH;
  const fx = (j: number) => x(hist.length + j);

  const band =
    fc.map((w, j) => `${j === 0 ? "M" : "L"}${fx(j)},${y(w.demand_high)}`).join(" ") +
    " " +
    [...fc]
      .reverse()
      .map((w, k) => `L${fx(fc.length - 1 - k)},${y(w.demand_low)}`)
      .join(" ") +
    " Z";
  const expected = fc.map((w, j) => `${j === 0 ? "M" : "L"}${fx(j)},${y(w.demand_expected)}`).join(" ");
  const dividerX = PAD.l + slot * hist.length;
  const ticks = [0, max / 2, max].map((v) => Math.round(v));
  const stockoutWeeks = hist.filter((h) => h.stockout_days > 0).length;

  return (
    <figure className="flex flex-col gap-1">
      <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label={`Weekly demand for ${forecast.name}: history and forecast`}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} className="stroke-border" strokeWidth={1} />
            <text x={PAD.l - 6} y={y(t) + 3} textAnchor="end" className="fill-muted-foreground text-[10px]">
              {fmtNum(t)}
            </text>
          </g>
        ))}
        {hist.map((h, i) => {
          const bw = slot * 0.7;
          const out = h.stockout_days > 0;
          return (
            <g key={h.week_start}>
              <rect
                x={x(i) - bw / 2}
                y={y(h.consumption)}
                width={bw}
                height={Math.max(0, PAD.t + plotH - y(h.consumption))}
                rx={1.5}
                fill={out ? "#dc2626" : "#94a3b8"}
                opacity={out ? 0.85 : 0.7}
              >
                <title>
                  {`Week of ${shortDate(h.week_start)}: ${h.consumption} ${forecast.unit}s used${out ? `, ${h.stockout_days} stock-out day(s)` : ""}`}
                </title>
              </rect>
              {out && (
                <text x={x(i)} y={y(h.consumption) - 3} textAnchor="middle" className="fill-red-600 text-[9px] font-semibold">
                  SO
                </text>
              )}
            </g>
          );
        })}
        <path d={band} fill="#2563eb" opacity={0.15} />
        <path d={expected} fill="none" stroke="#2563eb" strokeWidth={2} />
        {fc.map((w, j) => (
          <circle key={w.week_start} cx={fx(j)} cy={y(w.demand_expected)} r={2.5} fill="#2563eb">
            <title>{`Week of ${shortDate(w.week_start)}: expected ${fmtNum(w.demand_expected)} (range ${fmtNum(w.demand_low)}–${fmtNum(w.demand_high)})`}</title>
          </circle>
        ))}
        <line x1={dividerX} x2={dividerX} y1={PAD.t} y2={PAD.t + plotH} stroke="currentColor" strokeDasharray="3 3" opacity={0.5} />
        <text x={dividerX + 4} y={PAD.t + 9} className="fill-muted-foreground text-[10px]">
          forecast →
        </text>
        {hist[0] && (
          <text x={x(0)} y={H - 10} textAnchor="start" className="fill-muted-foreground text-[10px]">
            {shortDate(hist[0].week_start)}
          </text>
        )}
        {fc[0] && (
          <text x={fx(0)} y={H - 10} textAnchor="middle" className="fill-muted-foreground text-[10px]">
            {shortDate(fc[0].week_start)}
          </text>
        )}
        {fc.length > 1 && (
          <text x={fx(fc.length - 1)} y={H - 10} textAnchor="end" className="fill-muted-foreground text-[10px]">
            {shortDate(fc[fc.length - 1].week_start)}
          </text>
        )}
      </svg>
      <figcaption className="flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-muted-foreground">
        <span>Weekly {forecast.unit}s</span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block size-2.5 bg-slate-400" /> used (last 12 weeks)
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block size-2.5 bg-red-600" /> week with stock-out days (SO){stockoutWeeks ? `: ${stockoutWeeks}` : ""}
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block h-0.5 w-4 bg-blue-600" /> expected
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="inline-block size-2.5 bg-blue-600/15" /> 80% range
        </span>
      </figcaption>
      <p className="text-[11px] text-muted-foreground">
        {forecast.model.id}@{forecast.model.version} ({forecast.model.backend}
        {forecast.model.is_demo ? ", demo" : ""}) · {forecast.note}
      </p>
    </figure>
  );
}
