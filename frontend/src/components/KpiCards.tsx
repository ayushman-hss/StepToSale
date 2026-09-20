import type { Kpis, HourlyPoint } from '../types';
import { ThresholdBar } from '../lib/ui/ThresholdBar';
import { Figure } from '../lib/ui/controls';

const rupees = (n: number) =>
  `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

/**
 * Replaces the four identical bordered stat cards.
 *
 * Conversion is the product's whole thesis, so it gets the hero treatment and
 * a threshold bar measured against the store's own best hour -- a target the
 * shopkeeper has already proved is reachable. The other three figures are
 * plain: label under the number, sentence case, no box.
 */
export function KpiCards({ kpis, hourly }: { kpis: Kpis; hourly: HourlyPoint[] }) {
  const conversion = kpis.conversion_rate * 100;

  const busy = hourly.filter((h) => h.footfall > 0);
  const best = busy.length
    ? busy.reduce((a, b) => (b.conversion > a.conversion ? b : a))
    : null;
  const bestPct = best ? best.conversion * 100 : 0;
  const scale = Math.max(bestPct, conversion) * 1.15 || 1;

  return (
    <div className="space-y-7">
      <div>
        <p className="text-body text-muted">Of everyone who walked in</p>
        <p className="mt-1">
          <span className="tnum text-figure font-bold tracking-tight text-ink">
            {conversion.toFixed(1)}%
          </span>{' '}
          <span className="text-heading font-medium text-ink">bought something</span>
        </p>

        <div className="mt-4 max-w-xl">
          <ThresholdBar
            value={conversion}
            max={scale}
            threshold={bestPct || undefined}
            thresholdLabel={best ? `best hour ${bestPct.toFixed(1)}%` : undefined}
            minLabel="0%"
            maxLabel={`${scale.toFixed(0)}%`}
            caption={
              best
                ? `Your ${best.hour}:00 hour already converts at ${bestPct.toFixed(1)}%. Matching that all day is the target.`
                : undefined
            }
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-3 sm:max-w-xl">
        <Figure value={kpis.total_footfall.toLocaleString('en-IN')} label="visitors" />
        <Figure value={rupees(kpis.total_sales)} label="sales" />
        <Figure value={rupees(kpis.avg_basket)} label="per bill" />
      </div>
    </div>
  );
}
