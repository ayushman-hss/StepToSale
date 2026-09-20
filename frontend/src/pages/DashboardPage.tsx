import { useCallback, useEffect } from 'react';
import { useDashboard } from '../store';
import { fetchDashboard, fetchStores, uploadExcel } from '../api';
import { KpiCards } from '../components/KpiCards';
import { InsightCards } from '../components/InsightCards';
import { WhatsAppPreview } from '../components/WhatsAppPreview';
import { FilterBar } from '../components/FilterBar';
import { FootfallSalesChart } from '../components/FootfallSales';
import { ConversionChart } from '../components/ConversionChart';
import { Heatmap } from '../components/Heatmap';
import { FeatureSwitcher } from '../components/FeatureSwitcher';
import {
  EmptyState,
  Notice,
  PageHeader,
  Section,
  UploadButton,
} from '../lib/ui/controls';

export function DashboardPage() {
  const {
    data, loading, error, storeId, startDate, endDate,
    setData, setStores, setLoading, setError,
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
      setError(e instanceof Error ? e.message : 'Unknown error');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [storeId, startDate, endDate, setData, setStores, setLoading, setError]);

  useEffect(() => { load(); }, [load]);

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setLoading(true);
      setError(null);
      await uploadExcel(file);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  };

  return (
    <div>
      <PageHeader
        title="Sales vs footfall"
        lead="How many of the people who walk in actually buy, hour by hour."
        action={<UploadButton onChange={onUpload}>Upload your hours file</UploadButton>}
      />

      <div className="space-y-8">
        <FilterBar />

        {loading && !data && <p className="text-small text-muted">Loading&hellip;</p>}
        {error && <Notice>{error}</Notice>}

        {!data && !loading && !error && (
          <EmptyState title="Nothing to show yet">
            Upload a file with your hourly visitors, bills and sales to get started.
          </EmptyState>
        )}

        {data && (
          <>
            <KpiCards kpis={data.kpis} hourly={data.hourly} />

            <Section title="Visitors and sales, hour by hour">
              <FootfallSalesChart data={data.hourly} />
            </Section>

            <Section title="Share who bought, hour by hour">
              <ConversionChart data={data.hourly} />
            </Section>

            <Section title="Busiest times of the week">
              <Heatmap data={data.heatmap} />
            </Section>

            <InsightCards insights={data.insights} />

            <WhatsAppPreview text={data.whatsapp} />
          </>
        )}
      </div>

      <FeatureSwitcher
        to="/bundles"
        label="Bundles"
        description="Find the products your customers already buy together."
      />
    </div>
  );
}
