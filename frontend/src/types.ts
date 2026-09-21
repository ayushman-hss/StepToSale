export interface Kpis {
  total_footfall: number;
  total_sales: number;
  total_transactions: number;
  conversion_rate: number;
  avg_basket: number;
  sales_per_visitor: number;
}

/** An hour of the AVERAGE day when the range is longer than one day. */
export interface HourlyPoint {
  hour: number;
  footfall: number;
  sales: number;
  transactions: number;
  conversion: number;
}

export interface DailyPoint {
  date: string;
  footfall: number;
  sales: number;
  transactions: number;
  conversion: number;
}

export interface Insight {
  kind: 'warning' | 'opportunity' | 'observation' | 'win';
  text: string;
}

export interface Period {
  start: string;
  end: string;
  days: number;
  /** The range ends on a day still in progress (today). */
  partial: boolean;
  label: string;
}

/** The same weekday a week earlier, cut at the same hour. */
export interface Comparison {
  date: string;
  label: string;
  through_hour: number;
  footfall: number;
  transactions: number;
  sales: number;
}

export interface DashboardData {
  kpis: Kpis;
  hourly: HourlyPoint[];
  daily: DailyPoint[];
  insights: Insight[];
  whatsapp: string;
  heatmap: HeatmapPoint[];
  period: Period;
  /** Latest date and hour held for this shop, e.g. "2026-09-21T20". */
  data_through: string | null;
  compare: Comparison | null;
}

export interface Store {
  code: string;
  name: string;
}

export interface HeatmapPoint {
  dow: number;
  hour: number;
  footfall: number;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  cost_price: number;
  sell_price: number;
  margin_pct: number;
}

export interface BundleSuggestion {
  id: number;
  sku_a: string;
  sku_b: string;
  name_a: string;
  name_b: string;
  transactions_with_both: number;
  total_transactions: number;
  confidence: number;
  lift: number;
  separate_price: number;
  separate_margin_pct: number;
  suggested_price: number;
  suggested_margin_pct: number;
  margin_floor_pct: number;
  status: 'pending' | 'approved' | 'rejected';
  approved_price: number | null;
}
// ---- group-buying pools -------------------------------------------------
// Every monetary field below is an integer number of PAISE, never rupees.
// Format with formatPaise(); never do arithmetic on the rupee string.

export type PoolStrategy = 'unit_price' | 'pro_rata' | 'shapley';
export type PoolStatus = 'draft' | 'open' | 'locked' | 'settled' | 'cancelled';

export interface PoolTier {
  min_qty: number;
  max_qty: number | null;
  unit_price: number;
  label: string;
}

export interface PoolStoreLine {
  store: string;
  qty: number;
  cost_alone: number;
  payable: number;
  savings: number;
}

export interface PoolProduct {
  sku: string;
  name: string;
  supplier_id: string;
  price_list_version: string;
  total_qty: number;
  pooled_unit_price: number;
  tier_label: string;
  units_to_next_tier: number | null;
  next_tier_unit_price: number | null;
  invoice_total: number;
  total_savings: number;
  tiers: PoolTier[];
  lines: PoolStoreLine[];
}

export interface PoolStore {
  store: string;
  cost_alone: number;
  payable: number;
  savings: number;
  savings_pct: number;
}

export interface PoolDetail {
  code: string;
  name: string;
  status: PoolStatus;
  strategy: PoolStrategy;
  rotation: number;
  closes_at: string | null;
  invoice_total: number;
  total_savings: number;
  products: PoolProduct[];
  stores: PoolStore[];
}

export interface PoolEvent {
  actor: string;
  kind: string;
  detail: string;
  created_at: string;
}
