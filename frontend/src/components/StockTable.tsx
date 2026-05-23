import type { StockSignal } from "../types";

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
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Price</th>
            <th>RSI</th>
            <th>MACD</th>
            <th>Signal</th>
            <th>SMA 20</th>
            <th>SMA 50</th>
            <th>5d %</th>
            <th>20d %</th>
            <th>Score</th>
            <th>Signals</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
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
                  <strong>{row.symbol.replace(".NS", "")}</strong>
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
