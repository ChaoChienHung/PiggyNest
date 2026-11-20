import React, { createContext, useContext, useEffect, useState } from 'react';

export type ThemeMode = 'light' | 'dark';

interface ThemeContextValue {
    theme: ThemeMode;
    setTheme: (next: ThemeMode) => void;
    toggleTheme: () => void;
}

const STORAGE_KEY = 'piggynest-theme';

const ThemeContext = createContext<ThemeContextValue>({
    theme: 'light',
    setTheme: () => {},
    toggleTheme: () => {},
});

const getInitialTheme = (): ThemeMode => {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored === 'dark' || stored === 'light') return stored;
    } catch {
        // Ignore storage errors in restricted contexts
    }
    return 'light';
};

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [theme, setThemeState] = useState<ThemeMode>(getInitialTheme);

    useEffect(() => {
        const root = document.documentElement;
        if (theme === 'dark') {
            root.setAttribute('data-theme', 'dark');
        } else {
            root.removeAttribute('data-theme');
        }
        const meta = document.querySelector('meta[name="theme-color"]');
        if (meta) {
            meta.setAttribute('content', theme === 'dark' ? '#1b141e' : '#fff8fa');
        }
        try {
            localStorage.setItem(STORAGE_KEY, theme);
        } catch {
            // Ignore storage errors
        }
    }, [theme]);

    const setTheme = (next: ThemeMode) => setThemeState(next);
    const toggleTheme = () => setThemeState((prev) => (prev === 'dark' ? 'light' : 'dark'));

    return (
        <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useTheme = () => useContext(ThemeContext);
