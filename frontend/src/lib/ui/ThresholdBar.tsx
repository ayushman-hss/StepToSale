import clsx from 'clsx';

interface Props {
  /** Where you actually are. */
  value: number;
  /** The top of the scale. */
  max: number;
  /** The line you are trying to clear. Omit when the goal IS the max. */
  threshold?: number;
  /** Sits under the threshold tick, e.g. "your average 16.2%". */
  thresholdLabel?: string;
  /** Sits under the left end, e.g. "0%". */
  minLabel?: string;
  /** Sits under the right end, e.g. "30%". */
  maxLabel?: string;
  /** Sentence under the whole bar. */
  caption?: React.ReactNode;
  /** Brass fill reframes the bar as "an opportunity", not "a result". */
  tone?: 'board' | 'brass';
  size?: 'md' | 'sm';
  className?: string;
}

/** Screen readers should hear "18", not "17.921716669978142". */
const round = (n: number) => (Number.isInteger(n) ? n : Number(n.toFixed(1)));

/**
 * The one loud component in the app.
 *
 * It appears on every page because every page is the same question: are you
 * above the line? Conversion against your average, margin against your floor,
 * pooled volume against the next price tier. Everything else in the system
 * stays quiet so this can carry the weight.
 */
export function ThresholdBar({
  value,
  max,
  threshold,
  thresholdLabel,
  minLabel,
  maxLabel,
  caption,
  tone = 'board',
  size = 'md',
  className,
}: Props) {
  const safeMax = max > 0 ? max : 1;
  const pct = Math.max(0, Math.min(100, (value / safeMax) * 100));
  const thresholdPct =
    threshold == null ? null : Math.max(0, Math.min(100, (threshold / safeMax) * 100));
  const cleared = threshold == null ? pct >= 100 : value >= threshold;

  return (
    <div className={className}>
      <div
        className={clsx(
          'relative w-full overflow-hidden rounded-track border border-rule bg-white',
          size === 'md' ? 'h-3' : 'h-2',
        )}
        style={{ borderRadius: 'var(--radius-track)' }}
        role="img"
        aria-label={
          threshold == null
            ? `${round(value)} of ${round(max)}`
            : `${round(value)}, with the line at ${round(threshold)}, on a scale to ${round(max)}`
        }
      >
        <div
          className={clsx(
            'h-full transition-[width] duration-500 ease-out',
            tone === 'brass' ? 'bg-brass' : 'bg-board',
          )}
          style={{ width: `${pct}%` }}
        />

        {/* Brass cap: you are over the line. */}
        {cleared && tone === 'board' && pct > 2 && (
          <div
            className="absolute top-0 h-full w-1.5 bg-brass transition-[left] duration-500 ease-out"
            style={{ left: `calc(${pct}% - 0.375rem)` }}
          />
        )}

        {/* The line itself. */}
        {thresholdPct != null && (
          <div
            className="absolute top-0 h-full w-[3px] bg-ink"
            style={{ left: `calc(${thresholdPct}% - 1.5px)` }}
          />
        )}
      </div>

      {(minLabel || maxLabel || thresholdLabel) && (
        <div className="relative mt-1.5 h-4 text-fine text-muted">
          {minLabel && <span className="absolute left-0">{minLabel}</span>}
          {maxLabel && <span className="absolute right-0">{maxLabel}</span>}
          {thresholdLabel && thresholdPct != null && (
            <span
              className="absolute -translate-x-1/2 whitespace-nowrap font-medium text-ink"
              style={{
                left: `${Math.min(88, Math.max(12, thresholdPct))}%`,
              }}
            >
              {thresholdLabel}
            </span>
          )}
        </div>
      )}

      {caption && <p className="mt-2 text-small text-muted">{caption}</p>}
    </div>
  );
}
