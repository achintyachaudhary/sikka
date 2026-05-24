import { useState } from "react";
import IpoTab from "./components/IpoTab";
import ScreenerTab from "./components/ScreenerTab";
import type { AppTab } from "./types";
import "./App.css";

export default function App() {
  const [tab, setTab] = useState<AppTab>("screener");

  return (
    <div className="container">
      <header>
        <div>
          <h1>NSE Stock Screener</h1>
          <p className="subtitle">
            {tab === "screener"
              ? "RSI · MACD · SMA · Momentum"
              : "Recent IPO listing performance"}
          </p>
        </div>
        <nav className="tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={tab === "screener"}
            className={tab === "screener" ? "tab active" : "tab"}
            onClick={() => setTab("screener")}
          >
            Screener
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === "ipo"}
            className={tab === "ipo" ? "tab active" : "tab"}
            onClick={() => setTab("ipo")}
          >
            IPO Tracker
          </button>
        </nav>
      </header>

      {tab === "screener" ? <ScreenerTab /> : <IpoTab />}

      <p className="disclaimer">
        For education only. Not financial advice. Holdings from NSE quarterly
        filings (FII/DII via XBRL); prices via yfinance.
      </p>
    </div>
  );
}
