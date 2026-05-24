import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  type IChartApi,
  type ISeriesApi,
} from "lightweight-charts";
import type { OhlcBar } from "../types/chart";
import { chartTheme } from "../utils/tradingView";

interface LightweightStockChartProps {
  bars: OhlcBar[];
  height?: number;
}

export default function LightweightStockChart({
  bars,
  height = 420,
}: LightweightStockChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const dark = chartTheme() === "dark";
    const chart = createChart(container, {
      width: container.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: dark ? "#1e271e" : "#ffffff" },
        textColor: dark ? "#e4ebe4" : "#1a1a1a",
      },
      grid: {
        vertLines: { color: dark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)" },
        horzLines: { color: dark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)" },
      },
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#2e7d32",
      downColor: "#ef4444",
      borderUpColor: "#2e7d32",
      borderDownColor: "#ef4444",
      wickUpColor: "#2e7d32",
      wickDownColor: "#ef4444",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth });
    });
    ro.observe(container);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current || !bars.length) return;
    seriesRef.current.setData(
      bars.map((b) => ({
        time: b.time as string & number,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      })),
    );
    chartRef.current?.timeScale().fitContent();
  }, [bars]);

  if (!bars.length) {
    return (
      <div className="chart-empty" style={{ height }}>
        No price data for this timeframe.
      </div>
    );
  }

  return <div ref={containerRef} className="lw-chart-container" style={{ height, width: "100%" }} />;
}
