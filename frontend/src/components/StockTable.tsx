import { useCallback } from "react";
import { useTableSort } from "../hooks/useTableSort";
import type { StockSignal } from "../types";
import HoldingPct from "./HoldingPct";
import SortableTh from "./SortableTh";
import SymbolLink from "./SymbolLink";

function fmtNum(v: number | null, digits = 2): string {
  if (v == null) return "—";
  return v.toFixed(digits);
}

function PctCell({ value }: { value: number | null }) {
  if (value == null) return <>—</>;
  const cls = value >= 0 ? "pct-pos" : "pct-neg";
  const sign = value >= 0 ? "+" : "";
  return (
    <span className={cls}>
      {sign}
      {value.toFixed(2)}%
    </span>
  );
}

function formatLabel(s: string): string {
  return s.replace(/_/g, " ");
}

interface StockTableProps {
  rows: StockSignal[];
}

export default function StockTable({ rows }: StockTableProps) {
  const getValue = useCallback((row: StockSignal, key: string) => {
    switch (key) {
      case "symbol":
        return row.symbol.replace(".NS", "");
      case "price":
        return row.price;
      case "rsi":
        return row.rsi;
      case "macd":
        return row.macd;
      case "macd_signal":
        return row.macd_signal;
      case "sma_20":
        return row.sma_20;
      case "sma_50":
        return row.sma_50;
      case "change_5d_pct":
        return row.change_5d_pct;
      case "change_20d_pct":
        return row.change_20d_pct;
      case "score":
        return row.score;
      case "promoter_holding_pct":
        return row.promoter_holding_pct;
      case "fii_holding_pct":
        return row.fii_holding_pct;
      case "dii_holding_pct":
        return row.dii_holding_pct;
      case "public_holding_pct":
        return row.public_holding_pct;
      case "institutional_holding_pct":
        return row.institutional_holding_pct;
      case "signals":
        return row.signals.length;
      default:
        return null;
    }
  }, []);

  const { sortedRows, sortKey, sortDir, toggleSort } = useTableSort(
    rows,
    "score",
    "desc",
    getValue,
  );

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <SortableTh
              label="Symbol"
              sortKey="symbol"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="Price"
              sortKey="price"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="RSI"
              sortKey="rsi"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="MACD"
              sortKey="macd"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="Signal"
              sortKey="macd_signal"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="SMA 20"
              sortKey="sma_20"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="SMA 50"
              sortKey="sma_50"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="5d %"
              sortKey="change_5d_pct"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="20d %"
              sortKey="change_20d_pct"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="Score"
              sortKey="score"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="Promoter %"
              sortKey="promoter_holding_pct"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="FII %"
              sortKey="fii_holding_pct"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="DII %"
              sortKey="dii_holding_pct"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="Public %"
              sortKey="public_holding_pct"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="Inst. %"
              sortKey="institutional_holding_pct"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="Signals"
              sortKey="signals"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row) => {
            const overbought = row.warnings.includes("rsi_overbought");
            const rowClass = overbought
              ? "overbought"
              : row.trend === "up"
                ? "bullish"
                : "";
            const scoreClass = row.score >= 7 ? "score high" : "score";

            return (
              <tr key={row.symbol} className={rowClass}>
                <td>
                  <SymbolLink symbol={row.symbol} />
                </td>
                <td>₹{fmtNum(row.price)}</td>
                <td>{fmtNum(row.rsi)}</td>
                <td>{fmtNum(row.macd, 4)}</td>
                <td>{fmtNum(row.macd_signal, 4)}</td>
                <td>{fmtNum(row.sma_20)}</td>
                <td>{fmtNum(row.sma_50)}</td>
                <td>
                  <PctCell value={row.change_5d_pct} />
                </td>
                <td>
                  <PctCell value={row.change_20d_pct} />
                </td>
                <td>
                  <span className={scoreClass}>{row.score}</span>
                </td>
                <td>
                  <HoldingPct value={row.promoter_holding_pct} />
                </td>
                <td>
                  <HoldingPct value={row.fii_holding_pct} />
                </td>
                <td>
                  <HoldingPct value={row.dii_holding_pct} />
                </td>
                <td>
                  <HoldingPct value={row.public_holding_pct} />
                </td>
                <td>
                  <HoldingPct value={row.institutional_holding_pct} />
                </td>
                <td>
                  <div className="tags">
                    {row.signals.map((s) => (
                      <span key={s} className="tag">
                        {formatLabel(s)}
                      </span>
                    ))}
                    {row.warnings.map((w) => (
                      <span key={w} className="tag warn">
                        {formatLabel(w)}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
