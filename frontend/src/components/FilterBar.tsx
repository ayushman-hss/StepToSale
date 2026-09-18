import { useDashboard } from '../store';

export function FilterBar() {
  const { stores, storeId, startDate, endDate, setFilters } = useDashboard();

  return (
    <div className="flex flex-wrap items-end gap-3 rounded-xl border bg-white p-4">
      <div className="flex flex-col gap-1">
        <label className="text-xs text-slate-500">Store</label>
        <select
          value={storeId}
          onChange={(e) => setFilters({ storeId: e.target.value })}
          className="rounded-md border px-3 py-1.5 text-sm bg-white"
        >
          <option value="all">All stores</option>
          {stores.map((s) => (
            <option key={s.code} value={s.code}>
              {s.name || s.code}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-slate-500">From</label>
        <input
          type="date"
          value={startDate}
          onChange={(e) => setFilters({ startDate: e.target.value })}
          className="rounded-md border px-3 py-1.5 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-slate-500">To</label>
        <input
          type="date"
          value={endDate}
          onChange={(e) => setFilters({ endDate: e.target.value })}
          className="rounded-md border px-3 py-1.5 text-sm"
        />
      </div>

      <button
        onClick={() => setFilters({ storeId: 'all', startDate: '', endDate: '' })}
        className="ml-auto text-xs text-slate-500 hover:text-slate-900"
      >
        Clear
      </button>
    </div>
  );
}