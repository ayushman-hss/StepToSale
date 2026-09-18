import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { HourlyPoint } from '../types';

export function ConversionChart({ data }: { data: HourlyPoint[] }) {
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
    const avg =
      nonEmpty.reduce((s, d) => s + d.conversion, 0) / (nonEmpty.length || 1);

    chart.setOption({
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const p = params[0];
          const row = data[p.dataIndex];
          return `<b>${row.hour}:00</b><br/>Conversion: ${(row.conversion * 100).toFixed(1)}%`;
        },
      },
      grid: { left: 50, right: 30, top: 20, bottom: 30 },
      xAxis: {
        type: 'category',
        data: data.map((d) => `${d.hour}:00`),
        axisLabel: { fontSize: 11 },
      },
      yAxis: {
        type: 'value',
        axisLabel: { formatter: (v: number) => `${(v * 100).toFixed(0)}%` },
      },
      series: [
        {
          type: 'line',
          data: data.map((d) => d.conversion),
          smooth: true,
          lineStyle: { width: 3, color: '#8b5cf6' },
          itemStyle: { color: '#8b5cf6' },
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: { type: 'dashed', color: '#64748b' },
            data: [{ yAxis: avg, label: { formatter: `avg ${(avg * 100).toFixed(1)}%` } }],
          },
        },
      ],
    });
  }, [data]);

  return <div ref={ref} className="h-72 w-full" />;
}