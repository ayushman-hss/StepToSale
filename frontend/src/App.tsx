import { useCallback, useEffect } from 'react';
import { useDashboard } from './store';
import { fetchDashboard, fetchStores, uploadExcel } from './api';
import { KpiCards } from './components/KpiCards';
import { InsightCards } from './components/InsightCards';
import { WhatsAppPreview } from './components/WhatsappPreview';
import { FilterBar } from './components/FilterBar';
import { FootfallSalesChart } from './components/FootfallSales';
import { ConversionChart } from './components/ConversionChart';
import { Heatmap } from './components/Heatmap';

export default function App() {
  const {
    data,
    loading,
    error,
    storeId,
    startDate,
    endDate,
    setData,
    setStores,
    setLoading,
    setError,
  } = useDashboard();

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [d, s] = await Promise.all([
        fetchDashboard({
          store_id: storeId,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
        }),
        fetchStores(),
      ]);
      setData(d);
      setStores(s);
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      setError(msg);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [storeId, startDate, endDate, setData, setStores, setLoading, setError]);

  useEffect(() => {
    load();
  }, [load]);

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setLoading(true);
      setError(null);
      await uploadExcel(file);
      await load();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setError(msg);
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b bg-white sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">Sales vs Footfall</h1>
            <p className="text-sm text-slate-500">Reactive dashboard · demo</p>
          </div>
          <label className="cursor-pointer rounded-lg bg-slate-900 text-white px-4 py-2 text-sm hover:bg-slate-800">
            Upload Excel
            <input
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              onChange={onUpload}
            />
          </label>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6 space-y-6">
        <FilterBar />

        {loading && <div className="text-sm text-slate-500">Loading…</div>}

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {!data && !loading && !error && (
          <div className="text-center py-16 text-slate-500">
            <p className="mb-2">No data yet.</p>
            <p className="text-sm">
              Upload <code>backend/sample-data.xlsx</code> to get started.
            </p>
          </div>
        )}

        {data && (
          <>
            <KpiCards kpis={data.kpis} />

            <div className="rounded-xl border bg-white p-4">
              <h2 className="text-sm font-medium mb-2">Footfall vs Sales by hour</h2>
              <FootfallSalesChart data={data.hourly} />
            </div>

            <div className="rounded-xl border bg-white p-4">
              <h2 className="text-sm font-medium mb-2">Conversion rate by hour</h2>
              <ConversionChart data={data.hourly} />
            </div>

            <div className="rounded-xl border bg-white p-4">
              <h2 className="text-sm font-medium mb-2">Footfall heatmap</h2>
              <Heatmap data={data.heatmap} />
            </div>

            <InsightCards insights={data.insights} />
            <WhatsAppPreview text={data.whatsapp} />
          </>
        )}
      </main>
    </div>
  );
}