import { create } from 'zustand';
import type { DashboardData, Store } from './types';

interface State {
  data: DashboardData | null;
  stores: Store[];
  loading: boolean;
  error: string | null;
  storeId: string;
  startDate: string;
  endDate: string;
  setData: (d: DashboardData | null) => void;
  setStores: (s: Store[]) => void;
  setLoading: (b: boolean) => void;
  setError: (e: string | null) => void;
  setFilters: (f: { storeId?: string; startDate?: string; endDate?: string }) => void;
}

export const useDashboard = create<State>((set) => ({
  data: null,
  stores: [],
  loading: false,
  error: null,
  storeId: 'all',
  startDate: '',
  endDate: '',
  setData: (data) => set({ data }),
  setStores: (stores) => set({ stores }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setFilters: (f) =>
    set((s) => ({
      storeId: f.storeId ?? s.storeId,
      startDate: f.startDate ?? s.startDate,
      endDate: f.endDate ?? s.endDate,
    })),
}));