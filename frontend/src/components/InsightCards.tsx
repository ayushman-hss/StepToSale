import { AlertTriangle, Lightbulb, Info, CheckCircle2 } from 'lucide-react';
import type { Insight } from '../types';

const STYLE = {
  warning:     { bg: 'bg-amber-50',   border: 'border-amber-200',   text: 'text-amber-900',   icon: 'text-amber-600',   Icon: AlertTriangle },
  opportunity: { bg: 'bg-blue-50',    border: 'border-blue-200',    text: 'text-blue-900',    icon: 'text-blue-600',    Icon: Lightbulb },
  observation: { bg: 'bg-slate-50',   border: 'border-slate-200',   text: 'text-slate-700',   icon: 'text-slate-500',   Icon: Info },
  win:         { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-900', icon: 'text-emerald-600', Icon: CheckCircle2 },
} as const;

export function InsightCards({ insights }: { insights: Insight[] }) {
  if (!insights.length) return null;

  return (
    <div className="space-y-2">
      <h2 className="text-sm font-medium text-slate-700">Insights</h2>
      {insights.map((ins, i) => {
        const s = STYLE[ins.kind] ?? STYLE.observation;
        const Icon = s.Icon;
        return (
          <div
            key={i}
            className={`flex items-start gap-3 rounded-xl border ${s.border} ${s.bg} p-4`}
          >
            <Icon className={`h-5 w-5 ${s.icon} mt-0.5 shrink-0`} />
            <p className={`text-sm ${s.text}`}>{ins.text}</p>
          </div>
        );
      })}
    </div>
  );
}