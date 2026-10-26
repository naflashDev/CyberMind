/**
 * @file Header.tsx
 * @author naflashDev
 * @brief Barra superior con toggle de sidebar, indicador de estado de backend y selector rápido de modo oscuro.
 */

import React, { useEffect, useState } from 'react';
import { Menu, Sun, Moon, ShieldCheck, AlertCircle } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { api } from '../../services/api';

interface HeaderProps {
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  title: string;
}

export const Header: React.FC<HeaderProps> = ({ collapsed, setCollapsed, title }) => {
  const { mode, toggleMode } = useTheme();
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await api.getHealth();
        setIsHealthy(res.status === 'healthy');
      } catch {
        setIsHealthy(false);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)] px-6 flex items-center justify-between z-20">
      <div className="flex items-center gap-4">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)] hover:text-[var(--text-primary)] transition-all btn-bounce"
          title="Colapsar / expandir menú"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="text-lg font-bold text-[var(--text-primary)] tracking-tight">{title}</h1>
      </div>

      <div className="flex items-center gap-4">
        {/* Backend health status badge */}
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border ${
            isHealthy === true
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : isHealthy === false
              ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
              : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
          }`}
        >
          {isHealthy === true ? (
            <>
              <ShieldCheck className="w-4 h-4" />
              <span>Backend Conectado</span>
            </>
          ) : isHealthy === false ? (
            <>
              <AlertCircle className="w-4 h-4" />
              <span>Backend Desconectado</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
              <span>Verificando...</span>
            </>
          )}
        </div>

        {/* Dark / Light Mode Switch */}
        <button
          onClick={toggleMode}
          className="p-2.5 rounded-xl border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--brand-primary)] hover:border-[var(--brand-primary)]/40 transition-all btn-bounce bg-[var(--bg-surface-subtle)]"
          title={mode === 'dark' ? 'Cambiar a Modo Claro' : 'Cambiar a Modo Oscuro'}
        >
          {mode === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-500" />}
        </button>
      </div>
    </header>
  );
};
