import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import { useTheme } from "../hooks/useTheme";

export default function AppShell() {
  const [theme, toggleTheme] = useTheme();

  return (
    <div className="app-shell">
      <Sidebar theme={theme} onToggleTheme={toggleTheme} />
      <div className="app-main">
        <div className="app-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
