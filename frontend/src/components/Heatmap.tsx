import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { HeatmapPoint } from '../types';
import { CHART, baseOption, categoryAxis } from '../lib/charts/theme';

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

    chart.setOption(
      {
        ...baseOption({ left: 42, right: 14 }),
        grid: { left: 42, right: 14, top: 12, bottom: 48, containLabel: false },
        tooltip: {
          ...baseOption().tooltip,
          trigger: 'item',
          position: 'top',
          formatter: (p: unknown) => {
            const v = (p as { value: [number, number, number] }).value;
            return `${DAYS[v[1]]} ${hours[v[0]]}:00<br/>${v[2]} visitors`;
          },
        },
        xAxis: { ...categoryAxis(hours.map((h) => `${h}:00`)), splitArea: { show: false } },
        yAxis: {
          type: 'category',
          data: DAYS,
          axisLine: { show: false },
          axisTick: { show: false },
          splitArea: { show: false },
          axisLabel: { color: CHART.muted, fontSize: 11.5, fontFamily: CHART.font },
        },
        // One hue, ramped. A multi-hue scale would imply categories that
        // are not there -- this is one quantity getting bigger.
        visualMap: {
          min: 0,
          max: maxVal,
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: 0,
          itemWidth: 12,
          itemHeight: 90,
          textStyle: { color: CHART.muted, fontFamily: CHART.font, fontSize: 11.5 },
          inRange: { color: [CHART.white, CHART.boardTint, CHART.boardSoft, CHART.board] },
        },
        series: [
          {
            type: 'heatmap',
            data: data.map((d) => [hours.indexOf(d.hour), d.dow, d.footfall]),
            itemStyle: { borderColor: CHART.white, borderWidth: 1.5 },
            emphasis: { itemStyle: { borderColor: CHART.ink, borderWidth: 1.5 } },
          },
        ],
      },
      true,
    );
  }, [data]);

  return <div ref={ref} className="h-72 w-full" />;
}
