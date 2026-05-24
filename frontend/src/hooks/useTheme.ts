import { useEffect, useState, useCallback } from "react";

type Theme = "light" | "dark";

const STORAGE_KEY = "app_theme";

function applyTheme(theme: Theme) {
  document.documentElement.setAttribute("data-theme", theme);
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // ignore
  }
}

async function syncThemeToServer(theme: Theme) {
  try {
    await fetch("/api/preferences", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ preferences: { theme } }),
    });
  } catch {
    // offline or server not running — fine, localStorage still works
  }
}

async function loadThemeFromServer(): Promise<Theme | null> {
  try {
    const res = await fetch("/api/preferences");
    if (!res.ok) return null;
    const data = await res.json();
    const t = data?.preferences?.theme;
    if (t === "light" || t === "dark") return t;
  } catch {
    // ignore
  }
  return null;
}

export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
      if (stored === "light" || stored === "dark") return stored;
    } catch {
      // ignore
    }
    return "light";
  });

  // Apply on first render
  useEffect(() => {
    applyTheme(theme);
    // Try to load persisted theme from server; override if different
    loadThemeFromServer().then((serverTheme) => {
      if (serverTheme && serverTheme !== theme) {
        setTheme(serverTheme);
        applyTheme(serverTheme);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggle = useCallback(() => {
    setTheme((prev) => {
      const next: Theme = prev === "light" ? "dark" : "light";
      applyTheme(next);
      syncThemeToServer(next);
      return next;
    });
  }, []);

  return [theme, toggle];
}
