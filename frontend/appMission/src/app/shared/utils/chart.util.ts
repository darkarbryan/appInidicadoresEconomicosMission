import { Chart, ChartConfiguration, registerables } from 'chart.js';

let registered = false;

/**
 * Ensure Chart.js controllers/elements are registered once.
 */
export function ensureChartJs(): void {
  if (!registered) {
    Chart.register(...registerables);
    registered = true;
  }
}

/**
 * Destroy a chart instance if it exists.
 */
export function destroyChart(chart: Chart | null | undefined): void {
  chart?.destroy();
}

/**
 * Create a Chart.js instance on a canvas element (browser only).
 */
export function createChart(
  canvas: HTMLCanvasElement | null | undefined,
  config: ChartConfiguration,
): Chart | null {
  if (typeof window === 'undefined' || !canvas) {
    return null;
  }

  ensureChartJs();

  // Force a layout pass so Chart.js gets a non-zero size on first paint.
  const parent = canvas.parentElement;
  if (parent && parent.clientHeight === 0) {
    parent.style.minHeight = '260px';
  }

  return new Chart(canvas, config);
}
