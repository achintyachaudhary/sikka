import { useCallback } from "react";
import { useTableSort } from "../hooks/useTableSort";
import type { IpoListing } from "../types";
import HoldingPct from "./HoldingPct";
import SortableTh from "./SortableTh";

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

interface IpoTableProps {
  rows: IpoListing[];
}

export default function IpoTable({ rows }: IpoTableProps) {
  const getValue = useCallback((row: IpoListing, key: string) => {
    switch (key) {
      case "symbol":
        return row.symbol;
      case "company_name":
        return row.company_name;
      case "security_type":
        return row.security_type;
      case "listing_date":
        return row.listing_date;
      case "issue_price":
        return row.issue_price;
      case "listing_close":
        return row.listing_close;
      case "current_price":
        return row.current_price;
      case "listing_day_gain_pct":
        return row.listing_day_gain_pct;
      case "gain_vs_issue_pct":
        return row.gain_vs_issue_pct;
      case "gain_vs_listing_close_pct":
        return row.gain_vs_listing_close_pct;
      case "promoter_holding_pct":
        return row.promoter_holding_pct;
      case "fii_holding_pct":
        return row.fii_holding_pct;
      case "dii_holding_pct":
        return row.dii_holding_pct;
      case "public_holding_pct":
        return row.public_holding_pct;
      default:
        return null;
    }
  }, []);

  const { sortedRows, sortKey, sortDir, toggleSort } = useTableSort(
    rows,
    "listing_date",
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
              label="Company"
              sortKey="company_name"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="Type"
              sortKey="security_type"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="Listed"
              sortKey="listing_date"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="Issue ₹"
              sortKey="issue_price"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="List close ₹"
              sortKey="listing_close"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="Current ₹"
              sortKey="current_price"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="Day-1 %"
              sortKey="listing_day_gain_pct"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="vs Issue %"
              sortKey="gain_vs_issue_pct"
              activeKey={sortKey}
              direction={sortDir}
              onSort={toggleSort}
            />
            <SortableTh
              label="vs List close %"
              sortKey="gain_vs_listing_close_pct"
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
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row) => {
            const noData = row.status === "no_market_data";
            const rowClass = noData
              ? ""
              : (row.gain_vs_issue_pct ?? 0) >= 0
                ? "bullish"
                : "overbought";

            return (
              <tr key={`${row.symbol}-${row.listing_date}`} className={rowClass}>
                <td>
                  <strong>{row.symbol}</strong>
                </td>
                <td className="company-cell" title={row.company_name}>
                  {row.company_name}
                </td>
                <td>{row.security_type || "—"}</td>
                <td>{row.listing_date_display || row.listing_date}</td>
                <td>{fmtNum(row.issue_price)}</td>
                <td>{fmtNum(row.listing_close)}</td>
                <td>{fmtNum(row.current_price)}</td>
                <td>
                  <PctCell value={row.listing_day_gain_pct} />
                </td>
                <td>
                  <PctCell value={row.gain_vs_issue_pct} />
                </td>
                <td>
                  <PctCell value={row.gain_vs_listing_close_pct} />
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
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
