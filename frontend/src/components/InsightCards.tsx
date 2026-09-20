import { AlertTriangle, Lightbulb, Info, CheckCircle2 } from 'lucide-react';
import clsx from 'clsx';
import type { Insight } from '../types';

/**
 * Four kinds, three colours. Brass covers both "watch this" and "here is an
 * opportunity" because in this app they are the same instruction to the
 * shopkeeper: look here. Clay is reserved for actual problems, board for
 * things already going well.
 */
const STYLE = {
  warning: { edge: 'bg-clay', icon: 'text-clay', Icon: AlertTriangle },
  opportunity: { edge: 'bg-brass', icon: 'text-brass-deep', Icon: Lightbulb },
  win: { edge: 'bg-board', icon: 'text-board', Icon: CheckCircle2 },
  observation: { edge: 'bg-rule', icon: 'text-muted', Icon: Info },
} as const;

export function InsightCards({ insights }: { insights: Insight[] }) {
  if (!insights.length) return null;

  return (
    <section className="space-y-3">
      <h2 className="text-heading">What stands out</h2>
      <ul className="space-y-2">
        {insights.map((ins, i) => {
          const s = STYLE[ins.kind] ?? STYLE.observation;
          const Icon = s.Icon;
          return (
            <li
              key={i}
              className="relative flex items-start gap-3 overflow-hidden rounded-item border border-rule bg-white py-3.5 pl-5 pr-4"
            >
              <span className={clsx('absolute inset-y-0 left-0 w-1', s.edge)} aria-hidden />
              <Icon size={18} className={clsx('mt-0.5 shrink-0', s.icon)} aria-hidden />
              <p className="text-body text-ink">{ins.text}</p>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
