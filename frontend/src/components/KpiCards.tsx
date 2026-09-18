import type { Kpis } from '../types';

export function KpiCards({ kpis }: { kpis: Kpis }) {
  const items = [
    { label: 'Footfall', value: kpis.total_footfall.toLocaleString() },
    {
      label: 'Sales',
      value: `₹${kpis.total_sales.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`,
    },
    { label: 'Conversion', value: `${(kpis.conversion_rate * 100).toFixed(1)}%` },
    { label: 'Avg Basket', value: `₹${kpis.avg_basket.toFixed(0)}` },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {items.map((it) => (
        <div key={it.label} className="rounded-xl border bg-white p-4">
          <div className="text-xs uppercase tracking-wide text-slate-500">{it.label}</div>
          <div className="text-2xl font-semibold mt-1">{it.value}</div>
        </div>
      ))}
    </div>
  );
}