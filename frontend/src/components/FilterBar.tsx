import { useDashboard, type RangePreset } from '../store';
import { Select, Input, Segmented } from '../lib/ui/controls';

const PERIODS: { value: RangePreset; label: string }[] = [
  { value: 'today', label: 'Today' },
  { value: 'yesterday', label: 'Yesterday' },
  { value: '7d', label: 'Last 7 days' },
  { value: '28d', label: 'Last 4 weeks' },
  { value: 'all', label: 'All' },
  { value: 'custom', label: 'Pick dates' },
];

export function FilterBar() {
  const { stores, storeId, preset, startDate, endDate, setFilters, setPreset } =
    useDashboard();

  // Two or three shops is a segmented control, not a dropdown: fewer taps and
  // no hidden state. Past that it has to collapse into a select.
  const asSegments = stores.length > 0 && stores.length <= 3;

  return (
    <div className="space-y-4 rounded-section border border-rule bg-white p-4 md:p-5">
      <div className="flex flex-wrap items-end gap-4">
        {asSegments ? (
          <Segmented
            label="Shop"
            value={storeId}
            onChange={(v) => setFilters({ storeId: v })}
            options={[
              { value: 'all', label: 'All' },
              // Codes, not names: a segment has to stay narrow, and the rest
              // of the app refers to shops as S1/S2/S3 anyway.
              ...stores.map((s) => ({ value: s.code, label: s.code })),
            ]}
            size="sm"
          />
        ) : (
          <Select
            label="Shop"
            value={storeId}
            onChange={(e) => setFilters({ storeId: e.target.value })}
            className="min-w-40"
          >
            <option value="all">All shops</option>
            {stores.map((s) => (
              <option key={s.code} value={s.code}>
                {s.name || s.code}
              </option>
            ))}
          </Select>
        )}

        <Segmented
          label="Period"
          value={preset}
          onChange={setPreset}
          options={PERIODS}
          size="sm"
        />
      </div>

      {/* Raw date boxes only when asked for: most days the question is
          "how is today going", which should be one tap, not two pickers. */}
      {preset === 'custom' && (
        <div className="grid grid-cols-2 gap-3 sm:max-w-sm">
          <Input
            label="From"
            type="date"
            value={startDate}
            max={endDate || undefined}
            onChange={(e) => setFilters({ startDate: e.target.value })}
          />
          <Input
            label="To"
            type="date"
            value={endDate}
            min={startDate || undefined}
            onChange={(e) => setFilters({ endDate: e.target.value })}
          />
        </div>
      )}
    </div>
  );
}
