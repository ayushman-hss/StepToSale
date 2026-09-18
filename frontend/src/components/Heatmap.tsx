import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { HeatmapPoint } from '../types';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export function Heatmap({ data }: { data: HeatmapPoint[] }) {
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

    const hours = Array.from(new Set(data.map((d) => d.hour))).sort((a, b) => a - b);
    const maxVal = Math.max(...data.map((d) => d.footfall), 1);

    chart.setOption({
      tooltip: {
        position: 'top',
        formatter: (p: any) =>
          `${DAYS[p.value[1]]} ${hours[p.value[0]]}:00<br/>Footfall: ${p.value[2]}`,
      },
      grid: { left: 50, right: 20, top: 20, bottom: 40 },
      xAxis: {
        type: 'category',
        data: hours.map((h) => `${h}:00`),
        splitArea: { show: true },
        axisLabel: { fontSize: 10 },
      },
      yAxis: {
        type: 'category',
        data: DAYS,
        splitArea: { show: true },
        axisLabel: { fontSize: 11 },
      },
      visualMap: {
        min: 0,
        max: maxVal,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: 0,
        inRange: { color: ['#f1f5f9', '#93c5fd', '#2563eb'] },
      },
      series: [
        {
          type: 'heatmap',
          data: data.map((d) => [hours.indexOf(d.hour), d.dow, d.footfall]),
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' },
          },
        },
      ],
    });
  }, [data]);

  return <div ref={ref} className="h-72 w-full" />;
}