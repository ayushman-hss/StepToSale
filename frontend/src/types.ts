export interface Kpis {
  total_footfall: number;
  total_sales: number;
  total_transactions: number;
  conversion_rate: number;
  avg_basket: number;
  sales_per_visitor: number;
}

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

export interface DashboardData {
  kpis: Kpis;
  hourly: HourlyPoint[];
  daily: DailyPoint[];
  insights: Insight[];  
  whatsapp: string;
  heatmap: HeatmapPoint[];
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