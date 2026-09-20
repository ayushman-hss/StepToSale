/**
 * Shared ECharts styling.
 *
 * The charts have to obey the same rules as the DOM: board green carries the
 * data, brass only ever marks a threshold or a window worth noticing, and
 * nothing is decorated. Kept in one place so a palette change does not mean
 * editing three chart components.
 */
export const CHART = {
  ink: '#12211E',
  muted: '#5C6B66',
  rule: '#DDE2DC',
  board: '#0B5C4E',
  boardSoft: '#7FA79D',
  boardTint: '#E7EFEC',
  brass: '#E8A317',
  brassDeep: '#8A5B00',
  brassWash: 'rgba(232, 163, 23, 0.14)',
  clay: '#B3402B',
  white: '#FFFFFF',
  font: '"Anek Latin", ui-sans-serif, system-ui, sans-serif',
} as const;

/** Axis, grid and tooltip defaults every chart starts from. */
export function baseOption(opts: { left?: number; right?: number } = {}) {
  return {
    textStyle: { fontFamily: CHART.font },
    grid: {
      left: opts.left ?? 46,
      right: opts.right ?? 18,
      top: 24,
      bottom: 28,
      containLabel: false,
    },
    tooltip: {
      trigger: 'axis' as const,
      backgroundColor: CHART.ink,
      borderWidth: 0,
      padding: [8, 12] as [number, number],
      textStyle: { color: CHART.white, fontFamily: CHART.font, fontSize: 12.5 },
      extraCssText: 'border-radius:8px;box-shadow:none;',
    },
  };
}

export function categoryAxis(data: string[]) {
  return {
    type: 'category' as const,
    data,
    axisLine: { lineStyle: { color: CHART.rule } },
    axisTick: { show: false },
    axisLabel: { color: CHART.muted, fontSize: 11.5, fontFamily: CHART.font },
  };
}

export function valueAxis(extra: Record<string, unknown> = {}) {
  return {
    type: 'value' as const,
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: CHART.rule, type: 'solid' as const } },
    axisLabel: { color: CHART.muted, fontSize: 11.5, fontFamily: CHART.font },
    nameTextStyle: { color: CHART.muted, fontSize: 11.5, fontFamily: CHART.font },
    ...extra,
  };
}
