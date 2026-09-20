import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { HourlyPoint } from '../types';
import { CHART, baseOption, categoryAxis, valueAxis } from '../lib/charts/theme';

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

    const busy = data.filter((d) => d.footfall > 0);
    const peak = busy.reduce((a, b) => (b.footfall > a.footfall ? b : a), busy[0] ?? data[0]);

    chart.setOption(
      {
        ...baseOption({ left: 44, right: 50 }),
        tooltip: {
          ...baseOption().tooltip,
          formatter: (params: unknown) => {
            const p = (params as { dataIndex: number }[])[0];
            const row = data[p.dataIndex];
            return `<b>${row.hour}:00</b><br/>${row.footfall} visitors<br/>₹${row.sales.toLocaleString(
              'en-IN',
            )} sales<br/>${(row.conversion * 100).toFixed(1)}% bought`;
          },
        },
        xAxis: categoryAxis(data.map((d) => `${d.hour}:00`)),
        yAxis: [
          valueAxis(),
          valueAxis({
            position: 'right',
            splitLine: { show: false },
            axisLabel: {
              color: CHART.muted,
              fontSize: 11.5,
              fontFamily: CHART.font,
              formatter: (v: number) => `₹${(v / 1000).toFixed(0)}k`,
            },
          }),
        ],
        series: [
          {
            name: 'Visitors',
            type: 'bar',
            data: data.map((d) => d.footfall),
            itemStyle: { color: CHART.boardTint, borderRadius: [3, 3, 0, 0] },
            // Brass marks the window worth noticing -- the same meaning it
            // carries on every threshold bar in the app.
            markArea: peak
              ? {
                  silent: true,
                  itemStyle: { color: CHART.brassWash },
                  label: {
                    show: true,
                    position: 'insideTop',
                    color: CHART.brassDeep,
                    fontFamily: CHART.font,
                    fontSize: 11.5,
                    fontWeight: 600,
                    formatter: 'busiest',
                  },
                  data: [
                    [{ xAxis: `${peak.hour - 1}:00` }, { xAxis: `${peak.hour + 1}:00` }],
                  ],
                }
              : undefined,
          },
          {
            name: 'Sales',
            type: 'line',
            yAxisIndex: 1,
            data: data.map((d) => d.sales),
            smooth: true,
            symbol: 'none',
            lineStyle: { width: 2.5, color: CHART.board },
            itemStyle: { color: CHART.board },
          },
        ],
      },
      true,
    );
  }, [data]);

  return (
    <div>
      <div ref={ref} className="h-72 w-full md:h-80" />
      <p className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 text-small text-muted">
        <span className="inline-flex items-center gap-2">
          <span className="h-2.5 w-4 rounded-[2px] bg-board-tint" aria-hidden />
          visitors
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-0.5 w-4 rounded-full bg-board" aria-hidden />
          sales
        </span>
      </p>
    </div>
  );
}
