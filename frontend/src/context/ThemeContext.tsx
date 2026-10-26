/**
 * @file ThemeContext.tsx
 * @author naflashDev
 * @brief Proveedor de estado global para Apariencia, Paleta y Tipografía.
 * @details Gestiona la persistencia en localStorage y la aplicación de clases al elemento HTML raíz.
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import type { FontFamily, ThemeMode, ThemePalette, ThemeSettings } from '../types/theme';

interface ThemeContextType extends ThemeSettings {
  setPalette: (palette: ThemePalette) => void;
  setFont: (font: FontFamily) => void;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
}

const STORAGE_KEY = 'cybermind-theme-settings';

const defaultSettings: ThemeSettings = {
  palette: 'cyber-neon',
  font: 'plus-jakarta',
  mode: 'dark',
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<ThemeSettings>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch {
      // Fallback
    }
    return defaultSettings;
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));

    const root = document.documentElement;

    // Remove old theme classes
    root.classList.remove(
      'dark',
      'theme-cyber-neon',
      'theme-jetbrains-dark',
      'theme-amber-terminal',
      'theme-modern-saas',
      'theme-calma-organica',
      'theme-minimal-swiss',
      'font-plus-jakarta',
      'font-geist',
      'font-inter',
      'font-space-grotesk',
      'font-jetbrains-mono'
    );

    // Apply Mode
    if (settings.mode === 'dark') {
      root.classList.add('dark');
    }

    // Apply Palette
    root.classList.add(`theme-${settings.palette}`);

    // Apply Font
    root.classList.add(`font-${settings.font}`);
  }, [settings]);

  const setPalette = (palette: ThemePalette) => setSettings((s) => ({ ...s, palette }));
  const setFont = (font: FontFamily) => setSettings((s) => ({ ...s, font }));
  const setMode = (mode: ThemeMode) => setSettings((s) => ({ ...s, mode }));
  const toggleMode = () =>
    setSettings((s) => ({ ...s, mode: s.mode === 'dark' ? 'light' : 'dark' }));

  return (
    <ThemeContext.Provider
      value={{
        ...settings,
        setPalette,
        setFont,
        setMode,
        toggleMode,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
