import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import type { Theme } from "../types";

interface SidebarProps {
  theme: Theme;
  onToggleTheme: () => void;
}

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: "⊞", exact: true },
  { to: "/screener", label: "Screener", icon: "📊" },
  { to: "/ipo", label: "IPO Tracker", icon: "🚀" },
];

export default function Sidebar({ theme, onToggleTheme }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside className={`sidebar${collapsed ? " collapsed" : ""}`}>
      {/* Header */}
      <div className="sidebar-header">
        <div className="sidebar-logo">₹</div>
        {!collapsed && <span className="sidebar-brand">75 Rupee Gain</span>}
        <button
          type="button"
          className="sidebar-toggle"
          onClick={() => setCollapsed((c) => !c)}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? "▶" : "◀"}
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav" aria-label="Main navigation">
        {!collapsed && (
          <div className="sidebar-section-label">Menu</div>
        )}
        {NAV_ITEMS.map((item) => {
          const isActive = item.exact
            ? location.pathname === item.to
            : location.pathname.startsWith(item.to);
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={`sidebar-link${isActive ? " active" : ""}`}
              title={collapsed ? item.label : undefined}
            >
              <span className="nav-icon" aria-hidden="true">
                {item.icon}
              </span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <button
          type="button"
          className="sidebar-link"
          onClick={onToggleTheme}
          title={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
        >
          <span className="nav-icon" aria-hidden="true">
            {theme === "light" ? "🌙" : "☀️"}
          </span>
          <span className="nav-label">
            {theme === "light" ? "Dark Mode" : "Light Mode"}
          </span>
        </button>
      </div>
    </aside>
  );
}
