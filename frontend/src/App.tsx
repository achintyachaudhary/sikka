import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AppShell from "./components/AppShell";
import ScreenerPage from "./pages/ScreenerPage";
import IpoPage from "./pages/IpoPage";
import IpoResearchPage from "./pages/IpoResearchPage";
import DashboardPage from "./pages/DashboardPage";
import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="screener" element={<ScreenerPage />} />
          <Route path="ipo" element={<IpoPage />} />
          <Route path="ipo-research" element={<IpoResearchPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
