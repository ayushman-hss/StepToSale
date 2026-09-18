import type { DashboardData, Store } from './types';

export async function uploadExcel(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('/api/upload', { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? 'Upload failed');
  }
  return res.json();
}

export interface DashboardParams {
  store_id?: string;
  start_date?: string;
  end_date?: string;
}

export async function fetchDashboard(params: DashboardParams = {}): Promise<DashboardData> {
  const qs = new URLSearchParams();
  if (params.store_id && params.store_id !== 'all') qs.set('store_id', params.store_id);
  if (params.start_date) qs.set('start_date', params.start_date);
  if (params.end_date) qs.set('end_date', params.end_date);

  const res = await fetch(`/api/dashboard?${qs.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? 'Fetch failed');
  }
  return res.json();
}

export async function fetchStores(): Promise<Store[]> {
  const res = await fetch('/api/stores');
  if (!res.ok) return [];
  return res.json();
}