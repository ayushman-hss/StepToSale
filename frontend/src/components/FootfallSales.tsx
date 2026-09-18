import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { HourlyPoint } from '../types';

export function FootfallSalesChart({ data }: { data: HourlyPoint[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    chartRef.current = chart;

    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chart.dispose();
    };
  }, []);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart || !data.length) return;

    const nonEmpty = data.filter((d) => d.footfall > 0);
    const peak = nonEmpty.reduce(
      (a, b) => (b.footfall > a.footfall ? b : a),
      nonEmpty[0] ?? data[0]
    );

    chart.setOption({
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const p = params[0];
          const row = data[p.dataIndex];
          return `
            <div style="font-size:12px">
              <b>${row.hour}:00</b><br/>
              Footfall: ${row.footfall}<br/>
              Sales: ₹${row.sales.toLocaleString('en-IN')}<br/>
              Conversion: ${(row.conversion * 100).toFixed(1)}%
            </div>`;
        },
      },
      legend: { data: ['Footfall', 'Sales'], top: 0 },
      grid: { left: 50, right: 60, top: 40, bottom: 30 },
      xAxis: {
        type: 'category',
        data: data.map((d) => `${d.hour}:00`),
        axisLabel: { fontSize: 11 },
      },
      yAxis: [
        { type: 'value', name: 'Footfall', position: 'left' },
        {
          type: 'value',
          name: 'Sales (₹)',
          position: 'right',
          axisLabel: { formatter: (v: number) => `₹${(v / 1000).toFixed(0)}k` },
        },
      ],
      series: [
        {
          name: 'Footfall',
          type: 'bar',
          data: data.map((d) => d.footfall),
          itemStyle: { color: '#94a3b8', borderRadius: [4, 4, 0, 0] },
          markArea: peak
            ? {
                silent: true,
                itemStyle: { color: 'rgba(251, 191, 36, 0.15)' },
                data: [[{ xAxis: `${peak.hour - 1}:00` }, { xAxis: `${peak.hour + 1}:00` }]],
              }
            : undefined,
        },
        {
          name: 'Sales',
          type: 'line',
          yAxisIndex: 1,
          data: data.map((d) => d.sales),
          smooth: true,
          lineStyle: { width: 3, color: '#0ea5e9' },
          itemStyle: { color: '#0ea5e9' },
        },
      ],
    });
  }, [data]);

  return <div ref={ref} className="h-80 w-full" />;
}