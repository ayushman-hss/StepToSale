import type { Product } from '../types';
import { Badge } from '../lib/ui/controls';

const rupees = (n: number) => `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

/** Board = healthy, brass = thin, clay = below the floor most shops set. */
function marginTone(pct: number) {
  if (pct >= 0.25) return 'board' as const;
  if (pct >= 0.1) return 'brass' as const;
  return 'clay' as const;
}

export function ProductTable({ products }: { products: Product[] }) {
  return (
    <>
      {/* Phone: five columns will not fit, so each product is a row of its own. */}
      <ul className="divide-y divide-rule rounded-section border border-rule bg-white md:hidden">
        {products.map((p) => (
          <li key={p.id} className="flex items-start justify-between gap-3 p-4">
            <div className="min-w-0">
              <p className="truncate text-body font-medium text-ink">{p.name}</p>
              <p className="mt-0.5 text-small text-muted">
                {p.sku} &nbsp; costs {rupees(p.cost_price)} &nbsp; sells{' '}
                {rupees(p.sell_price)}
              </p>
            </div>
            <Badge tone={marginTone(p.margin_pct)}>
              {(p.margin_pct * 100).toFixed(0)}% kept
            </Badge>
          </li>
        ))}
      </ul>

      <div className="hidden overflow-hidden rounded-section border border-rule bg-white md:block">
        <table className="w-full text-body">
          <caption className="sr-only">Products with cost, selling price and margin</caption>
          <thead>
            <tr className="border-b border-rule text-left text-small text-muted">
              <th scope="col" className="px-5 py-3 font-medium">Code</th>
              <th scope="col" className="px-5 py-3 font-medium">Product</th>
              <th scope="col" className="px-5 py-3 text-right font-medium">You pay</th>
              <th scope="col" className="px-5 py-3 text-right font-medium">You charge</th>
              <th scope="col" className="px-5 py-3 text-right font-medium">You keep</th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} className="border-b border-rule last:border-0 hover:bg-chalk">
                <td className="px-5 py-3 text-small text-muted">{p.sku}</td>
                <td className="px-5 py-3 text-ink">{p.name}</td>
                <td className="px-5 py-3 text-right text-muted">{rupees(p.cost_price)}</td>
                <td className="px-5 py-3 text-right text-ink">{rupees(p.sell_price)}</td>
                <td className="px-5 py-3 text-right">
                  <Badge tone={marginTone(p.margin_pct)}>
                    {(p.margin_pct * 100).toFixed(1)}%
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
