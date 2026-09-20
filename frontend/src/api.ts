import type { DashboardData, Store } from './types';
import type { Product, BundleSuggestion } from './types';
import type { PoolDetail, PoolStrategy, PoolEvent as PoolEventRow } from './types';

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

export async function uploadProductCatalog(storeId: string, file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`/api/products/upload?store_id=${storeId}`, {
    method: 'POST', body: form,
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? 'Upload failed');
  return res.json();
}

export async function fetchProducts(storeId: string): Promise<Product[]> {
  const res = await fetch(`/api/products?store_id=${storeId}`);
  if (!res.ok) throw new Error('Failed to load products');
  return res.json();
}

export async function uploadSalesLines(
  storeId: string,
  file: File,
  mode: 'replace' | 'append' = 'replace',
) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(
    `/api/bundles/upload-lines?store_id=${storeId}&mode=${mode}`,
    { method: 'POST', body: form },
  );
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? 'Upload failed');
  return res.json();
}

export interface GenerateResult {
  suggestions: number;
  decisions_kept: number;
  baskets: number;
  min_support_tx: number;
  min_lift: number;
  unmatched_sku_count: number;
  unmatched_skus: string[];
  candidate_pairs?: number;
  dropped_missing_product?: number;
  dropped_no_discount?: number;
}

export async function generateBundles(
  storeId: string,
  marginFloorPct: number,
): Promise<GenerateResult> {
  const res = await fetch(
    `/api/bundles/generate?store_id=${storeId}&margin_floor_pct=${marginFloorPct}`,
    { method: 'POST' },
  );
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? 'Generate failed');
  return res.json();
}

export async function fetchBundles(storeId: string, status: string): Promise<BundleSuggestion[]> {
  const res = await fetch(`/api/bundles?store_id=${storeId}&status=${status}`);
  if (!res.ok) throw new Error('Failed to load bundles');
  return res.json();
}

export async function approveBundle(id: number, price?: number) {
  const res = await fetch(`/api/bundles/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ price }),
  });
  if (!res.ok) throw new Error('Approve failed');
  return res.json();
}

export async function rejectBundle(id: number) {
  const res = await fetch(`/api/bundles/${id}/reject`, { method: 'POST' });
  if (!res.ok) throw new Error('Reject failed');
  return res.json();
}
// ---- group-buying pools -------------------------------------------------

async function poolJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error((await res.json().catch(() => ({}))).detail ?? 'Request failed');
  }
  return res.json();
}

export async function fetchPool(
  code: string,
  strategy: PoolStrategy,
): Promise<PoolDetail> {
  return poolJson(await fetch(`/api/pools/${code}?strategy=${strategy}`));
}

export async function placePoolOrder(
  code: string,
  strategy: PoolStrategy,
  body: { store_id: string; sku: string; qty: number },
): Promise<PoolDetail> {
  return poolJson(
    await fetch(`/api/pools/${code}/orders?strategy=${strategy}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  );
}

export async function withdrawFromPool(
  code: string,
  strategy: PoolStrategy,
  body: { store_id: string; sku?: string },
): Promise<PoolDetail> {
  return poolJson(
    await fetch(`/api/pools/${code}/withdraw?strategy=${strategy}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  );
}

export async function closePool(
  code: string,
  strategy: PoolStrategy,
): Promise<PoolDetail> {
  return poolJson(
    await fetch(`/api/pools/${code}/close?strategy=${strategy}`, { method: 'POST' }),
  );
}

export async function reopenPool(
  code: string,
  strategy: PoolStrategy,
): Promise<PoolDetail> {
  return poolJson(
    await fetch(`/api/pools/${code}/reopen?strategy=${strategy}`, { method: 'POST' }),
  );
}

export async function fetchPoolEvents(code: string): Promise<PoolEventRow[]> {
  return poolJson(await fetch(`/api/pools/${code}/events`));
}
