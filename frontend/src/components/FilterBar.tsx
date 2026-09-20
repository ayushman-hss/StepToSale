import { useDashboard } from '../store';
import { Select, Input, Button, Segmented } from '../lib/ui/controls';

export function FilterBar() {
  const { stores, storeId, startDate, endDate, setFilters } = useDashboard();
  const dirty = storeId !== 'all' || startDate || endDate;

  // Two or three shops is a segmented control, not a dropdown: fewer taps and
  // no hidden state. Past that it has to collapse into a select.
  const asSegments = stores.length > 0 && stores.length <= 3;

  return (
    <div className="flex flex-wrap items-end gap-4 rounded-section border border-rule bg-white p-4 md:p-5">
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

      <Input
        label="From"
        type="date"
        value={startDate}
        onChange={(e) => setFilters({ startDate: e.target.value })}
        wrapClassName="min-w-36"
      />
      <Input
        label="To"
        type="date"
        value={endDate}
        onChange={(e) => setFilters({ endDate: e.target.value })}
        wrapClassName="min-w-36"
      />

      {dirty && (
        <Button
          variant="quiet"
          size="sm"
          onClick={() => setFilters({ storeId: 'all', startDate: '', endDate: '' })}
        >
          Show everything
        </Button>
      )}
    </div>
  );
}
