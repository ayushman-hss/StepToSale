import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { HourlyPoint } from '../types';
import { CHART, baseOption, categoryAxis, valueAxis } from '../lib/charts/theme';

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

    const busy = data.filter((d) => d.footfall > 0);
    const avg = busy.reduce((s, d) => s + d.conversion, 0) / (busy.length || 1);

    chart.setOption(
      {
        ...baseOption({ left: 44, right: 20 }),
        tooltip: {
          ...baseOption().tooltip,
          formatter: (params: unknown) => {
            const p = (params as { dataIndex: number }[])[0];
            const row = data[p.dataIndex];
            return `<b>${row.hour}:00</b><br/>${(row.conversion * 100).toFixed(1)}% bought`;
          },
        },
        xAxis: categoryAxis(data.map((d) => `${d.hour}:00`)),
        yAxis: valueAxis({
          axisLabel: {
            color: CHART.muted,
            fontSize: 11.5,
            fontFamily: CHART.font,
            formatter: (v: number) => `${(v * 100).toFixed(0)}%`,
          },
        }),
        series: [
          {
            type: 'line',
            data: data.map((d) => d.conversion),
            smooth: true,
            symbol: 'none',
            lineStyle: { width: 2.5, color: CHART.board },
            areaStyle: { color: CHART.boardTint, opacity: 0.7 },
            // The average line is this chart's threshold -- same idea as the
            // bar, drawn in ink because it is a reference, not a value.
            markLine: {
              silent: true,
              symbol: 'none',
              lineStyle: { type: 'dashed', color: CHART.ink, width: 1.5 },
              data: [
                {
                  yAxis: avg,
                  label: {
                    formatter: `your average ${(avg * 100).toFixed(1)}%`,
                    color: CHART.ink,
                    fontFamily: CHART.font,
                    fontSize: 11.5,
                    fontWeight: 600,
                    position: 'insideEndTop',
                  },
                },
              ],
            },
          },
        ],
      },
      true,
    );
  }, [data]);

  return <div ref={ref} className="h-64 w-full md:h-72" />;
}
