/**
 * Money arrives from the API as an integer number of paise and stays that way
 * until the moment it is rendered. Do not add, split or average the strings
 * this produces -- do that server-side, where the settlement invariants live.
 */
export function formatPaise(paise: number, opts: { compact?: boolean } = {}): string {
  const sign = paise < 0 ? '-' : '';
  const abs = Math.abs(paise);
  const rupees = Math.floor(abs / 100);
  const part = abs % 100;
  if (opts.compact && part === 0) {
    return `${sign}₹${rupees.toLocaleString('en-IN')}`;
  }
  return `${sign}₹${rupees.toLocaleString('en-IN')}.${String(part).padStart(2, '0')}`;
}
