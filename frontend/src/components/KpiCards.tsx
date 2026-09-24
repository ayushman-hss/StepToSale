import type { Comparison, Kpis, HourlyPoint, Period } from '../types';
import { ThresholdBar } from '../lib/ui/ThresholdBar';
import { Figure } from '../lib/ui/controls';

const rupees = (n: number) =>
  `₹${Math.abs(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

/**
 * Conversion is the product's thesis, so it gets the hero and a threshold bar
 * measured against the shop's own best hour -- a target already proved
 * reachable. The other figures are plain: label under the number, no box.
 */
export function KpiCards({
  kpis,
  hourly,
  period,
  compare,
}: {
  kpis: Kpis;
  hourly: HourlyPoint[];
  period: Period;
  compare: Comparison | null;
}) {
  const conversion = kpis.conversion_rate * 100;

  // Same rule as the insights on the server, so the page never names two
  // different "best hours": an hour must carry a real share of the traffic.
  const peak = Math.max(0, ...hourly.map((h) => h.footfall));
  const floor = Math.max(3, peak * 0.3);
  const busy = hourly.filter((h) => h.footfall >= floor);
  const top = busy.length
    ? busy.reduce((a, b) => (b.conversion > a.conversion ? b : a), busy[0])
    : null;
  // Only a target if it genuinely beats today's rate -- busy hours often
  // convert worst, and a "target" below where you already are is no target.
  const best = top && top.conversion * 100 > conversion * 1.05 ? top : null;
  const bestPct = best ? best.conversion * 100 : 0;
  const scale = Math.max(bestPct, conversion) * 1.15 || 1;

  // "Partial" only means "today so far" when today is the whole range; a
  // longer range that merely ends today still covers all its earlier days.
  const lead =
    period.days === 1
      ? period.partial
        ? 'Of everyone who walked in today so far'
        : `Of everyone who walked in on ${period.label}`
      : `Of everyone who walked in, ${period.label}${
          period.partial ? ', including today so far' : ''
        }`;

  return (
    <div className="space-y-7">
      <div>
        <p className="text-body text-muted">{lead}</p>
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
            thresholdLabel={best ? `best hour ${bestPct.toFixed(0)}%` : undefined}
            minLabel="0%"
            caption={
              best
                ? `Your ${best.hour}:00 hour converts at ${bestPct.toFixed(1)}%. Matching that all day is the target.`
                : 'None of your busy hours converts clearly better than this. Busy times tend to convert worst, so queues and browsing are the thing to watch.'
            }
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-6 gap-y-5 sm:max-w-xl sm:grid-cols-3">
        <Figure value={kpis.total_footfall.toLocaleString('en-IN')} label="visitors" />
        <Figure value={rupees(kpis.total_sales)} label="sales" />
        <Figure value={rupees(kpis.avg_basket)} label="per bill" />
      </div>

      {compare && <CompareLine kpis={kpis} compare={compare} partial={period.partial} />}
    </div>
  );
}

/**
 * Today on its own means little; today against the same weekday last week,
 * cut at the same hour, is the number a shopkeeper actually checks.
 */
function CompareLine({
  kpis,
  compare,
  partial,
}: {
  kpis: Kpis;
  compare: Comparison;
  partial: boolean;
}) {
  const diff = kpis.total_sales - compare.sales;
  const ahead = diff >= 0;
  const billsDiff = kpis.total_transactions - compare.transactions;

  return (
    <p className="max-w-xl rounded-item border border-rule bg-white px-4 py-3 text-body text-ink">
      {partial ? 'So far that is ' : 'That was '}
      <strong className={ahead ? 'font-semibold text-board' : 'font-semibold'}>
        {rupees(diff)} {ahead ? 'ahead of' : 'behind'}
      </strong>{' '}
      {compare.label}, with {kpis.total_transactions} bills against{' '}
      {compare.transactions}
      {billsDiff !== 0 && (
        <span className="text-muted">
          {' '}
          ({billsDiff > 0 ? `${billsDiff} more` : `${-billsDiff} fewer`})
        </span>
      )}
      .
    </p>
  );
}
