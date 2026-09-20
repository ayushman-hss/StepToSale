/**
 * The name already contains the motif: Step. And the volume-tier ladder in
 * Group Buying is literally a staircase. So the mark is three ascending
 * steps, with the top one in brass -- you cleared the line. Same geometry
 * and the same two colours as the ThresholdBar.
 */
export function StepsMark({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
      focusable="false"
    >
      <rect x="1" y="14" width="6" height="9" rx="1" className="fill-board" />
      <rect x="9" y="9" width="6" height="14" rx="1" className="fill-board" />
      <rect x="17" y="2" width="6" height="21" rx="1" className="fill-brass" />
    </svg>
  );
}

export function Wordmark({ size = 20 }: { size?: number }) {
  return (
    <span className="inline-flex items-center gap-2">
      <StepsMark size={size} />
      <span
        className="font-bold tracking-tight text-ink"
        style={{ fontSize: size * 0.85, letterSpacing: '-0.02em' }}
      >
        StepToSales
      </span>
    </span>
  );
}
