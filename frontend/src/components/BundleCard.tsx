import { useState } from 'react';
import { Check, X, Pencil, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';
import type { BundleSuggestion } from '../types';
import { ThresholdBar } from '../lib/ui/ThresholdBar';
import { Badge, Button, Input } from '../lib/ui/controls';

interface Props {
  bundle: BundleSuggestion;
  onApprove: (id: number, price?: number) => void;
  onReject: (id: number) => void;
}

const rupees = (n: number) => `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

/** Product names arrive as "Butter - Pasteurised"; a spaced dash is chrome. */
const clean = (name: string) =>
  name.replace(/\s+/g, ' ').replace(/ - /g, ', ');

export function BundleCard({ bundle, onApprove, onReject }: Props) {
  const [editing, setEditing] = useState(false);
  const [price, setPrice] = useState(bundle.suggested_price);

  const separateCost = bundle.separate_price * (1 - bundle.separate_margin_pct);
  const liveMargin = price > 0 ? (price - separateCost) / price : 0;
  const liveMarginAmount = price - separateCost;
  const belowFloor = liveMargin < bundle.margin_floor_pct;

  const displayPrice = editing ? price : bundle.suggested_price;
  const displayMargin = editing ? liveMargin : bundle.suggested_margin_pct;
  const displayMarginAmount = editing
    ? liveMarginAmount
    : bundle.suggested_price - separateCost;

  const floorPct = bundle.margin_floor_pct * 100;
  const marginPct = displayMargin * 100;
  const under = marginPct < floorPct;

  // The left edge says what this card wants from you at a glance.
  const edge =
    bundle.status === 'approved'
      ? 'bg-board'
      : bundle.status === 'rejected'
        ? 'bg-rule'
        : 'bg-brass';

  return (
    <article className="relative overflow-hidden rounded-item border border-rule bg-white">
      <span className={clsx('absolute inset-y-0 left-0 w-1', edge)} aria-hidden />

      <div className="space-y-4 py-5 pl-6 pr-5">
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-heading leading-snug text-ink">
            {clean(bundle.name_a)}{' '}
            <span className="font-normal text-muted">with</span>{' '}
            {clean(bundle.name_b)}
          </h3>
          {bundle.status === 'approved' && <Badge tone="board">Approved</Badge>}
          {bundle.status === 'rejected' && <Badge>Rejected</Badge>}
        </div>

        <div className="text-small text-muted">
          <p className="text-body text-ink">
            Bought together in{' '}
            <strong className="font-semibold">
              {Math.round(bundle.confidence * 100)}%
            </strong>{' '}
            of the bills that had either one.
          </p>
          <p className="mt-1">
            {bundle.lift.toFixed(1)}× more likely than chance
          </p>
          <p>
            {bundle.transactions_with_both} of {bundle.total_transactions} bills
          </p>
        </div>

        <dl className="space-y-1.5 rounded-item bg-chalk p-4 text-body">
          <div className="flex justify-between">
            <dt className="text-muted">Bought separately</dt>
            <dd className="tnum text-muted">{rupees(bundle.separate_price)}</dd>
          </div>
          <div className="flex justify-between font-semibold">
            <dt>As a bundle</dt>
            <dd className="tnum">{rupees(displayPrice)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted">You keep</dt>
            <dd
              className={clsx(
                'tnum font-semibold',
                under ? 'text-clay' : 'text-board',
              )}
            >
              {rupees(displayMarginAmount)} ({marginPct.toFixed(1)}%)
            </dd>
          </div>

          <div className="pt-2">
            <ThresholdBar
              size="sm"
              value={marginPct}
              max={Math.max(floorPct * 2.5, marginPct * 1.25, 1)}
              threshold={floorPct}
              thresholdLabel={`floor ${floorPct.toFixed(0)}%`}
            />
          </div>
        </dl>

        {editing && belowFloor && (
          <p className="flex items-start gap-2 rounded-item border border-clay/30 bg-clay-tint p-3 text-small text-clay">
            <AlertTriangle size={15} className="mt-0.5 shrink-0" aria-hidden />
            <span>
              At {rupees(price)} you would keep {rupees(liveMarginAmount)}, which is under
              your {floorPct.toFixed(0)}% floor.
            </span>
          </p>
        )}

        {bundle.status === 'approved' && bundle.approved_price != null && (
          <p className="text-small text-muted">
            Selling as a bundle at {rupees(bundle.approved_price)}.
          </p>
        )}

        {bundle.status === 'pending' &&
          (editing ? (
            <div className="flex flex-wrap items-end gap-2">
              <Input
                label="Bundle price"
                type="number"
                inputMode="numeric"
                value={price}
                onChange={(e) => setPrice(Number(e.target.value))}
                className="w-28"
                autoFocus
              />
              <Button
                onClick={() => {
                  onApprove(bundle.id, price);
                  setEditing(false);
                }}
                disabled={belowFloor}
              >
                <Check size={15} aria-hidden />
                Approve at {rupees(price)}
              </Button>
              <Button
                variant="quiet"
                onClick={() => {
                  setEditing(false);
                  setPrice(bundle.suggested_price);
                }}
              >
                Cancel
              </Button>
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              <Button onClick={() => onApprove(bundle.id)}>
                <Check size={15} aria-hidden />
                Approve
              </Button>
              <Button variant="secondary" onClick={() => setEditing(true)}>
                <Pencil size={15} aria-hidden />
                Change price
              </Button>
              <Button
                variant="quiet"
                className="ml-auto"
                onClick={() => onReject(bundle.id)}
              >
                <X size={15} aria-hidden />
                Reject
              </Button>
            </div>
          ))}
      </div>
    </article>
  );
}
