/**
 * @file Sidebar.tsx
 * @author naflashDev
 * @brief Main navigation sidebar replicating the exact sections of index.html with modern Lucide icons.
 * @details Includes Services, Datos, Noticias Tiny, CyberSentinel IA (conditionally visible), Documentación, Configuración, and Apagar app.
 */

import React, { useState } from 'react';
import {
  Zap,
  BarChart2,
  Newspaper,
  Bot,
  BookOpen,
  Settings,
  Shield,
  Power,
} from 'lucide-react';
import { api } from '../../services/api';

export type ActiveTab = 'fastapi' | 'datos' | 'tiny' | 'llm' | 'docs' | 'config';

interface SidebarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  useOllama: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  collapsed,
  useOllama,
}) => {
  const [shuttingDown, setShuttingDown] = useState(false);

  const navItems: Array<{
    id: ActiveTab;
    label: string;
    icon: React.FC<{ className?: string }>;
    visible?: boolean;
  }> = [
    { id: 'fastapi', label: 'Services', icon: Zap, visible: true },
    { id: 'datos', label: 'Datos', icon: BarChart2, visible: true },
    { id: 'tiny', label: 'Noticias Tiny', icon: Newspaper, visible: true },
    { id: 'llm', label: 'CyberSentinel IA', icon: Bot, visible: useOllama },
    { id: 'docs', label: 'Documentación', icon: BookOpen, visible: true },
    { id: 'config', label: 'Configuración', icon: Settings, visible: true },
  ];

  /**
   * @brief Handle application shutdown button click.
   */
  const handleShutdown = async () => {
    if (
      !window.confirm(
        '¿Seguro que deseas apagar la aplicación? Se cerrarán todos los servicios y procesos.'
      )
    ) {
      return;
    }
    setShuttingDown(true);
    try {
      const data = await api.shutdownApp();
      window.alert(
        'La aplicación se está apagando. Esta ventana dejará de responder en unos segundos.'
      );
      if (data && data.reload) {
        setTimeout(() => {
          window.location.reload();
        }, 5000);
      }
    } catch {
      window.alert('Error al solicitar el apagado.');
      setShuttingDown(false);
    }
  };

  return (
    <aside
      id="sidebar"
      className={`h-screen flex flex-col justify-between border-r border-[var(--border-subtle)] bg-[var(--bg-surface)] transition-all duration-300 z-30 select-none ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Top section: Title + Navigation + Shutdown */}
      <div>
        <div className="p-4 flex items-center justify-between border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-[var(--brand-primary)]/10 border border-[var(--brand-primary)]/30 flex items-center justify-center shrink-0">
              <Shield className="w-5 h-5 text-[var(--brand-primary)]" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <h1 className="font-bold text-base tracking-tight text-[var(--text-primary)] m-0">
                  CyberMind
                </h1>
                <span className="text-[10px] tracking-wider uppercase text-[var(--brand-primary)] font-semibold">
                  Security Suite v2.0
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Navigation Buttons */}
        <nav className="p-3 space-y-1.5">
          {navItems
            .filter((item) => item.visible !== false)
            .map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  id={`btn-${item.id}`}
                  data-view={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`nav-button w-full flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium text-sm transition-all btn-bounce ${
                    isActive
                      ? 'active bg-[var(--brand-primary)] text-white shadow-lg shadow-[var(--brand-primary)]/20 font-semibold'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)] hover:text-[var(--text-primary)]'
                  }`}
                  title={item.label}
                >
                  <Icon
                    className={`w-5 h-5 shrink-0 ${
                      isActive ? 'text-white' : 'text-[var(--text-muted)]'
                    }`}
                  />
                  {!collapsed && <span>{item.label}</span>}
                </button>
              );
            })}

          {/* Shutdown Button */}
          <div className="pt-4">
            <button
              id="btn-shutdown"
              onClick={handleShutdown}
              disabled={shuttingDown}
              title="Apagar la aplicación"
              className="shutdown-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl font-bold text-sm transition-all btn-bounce bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-600 hover:text-white disabled:opacity-50"
            >
              <Power className="w-5 h-5 shrink-0" />
              {!collapsed && <span>{shuttingDown ? 'Apagando...' : 'Apagar app'}</span>}
            </button>
          </div>
        </nav>
      </div>

      {/* Sidebar Footer */}
      <div className="p-4 border-t border-[var(--border-subtle)] text-center">
        {!collapsed ? (
          <div>
            <a
              href="https://github.com/naflashDev"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block"
            >
              <img
                src="/CyberMindLogo.webp"
                alt="CyberMind Logo"
                className="w-24 h-auto mx-auto mb-2 opacity-90 hover:opacity-100 transition-opacity"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            </a>
            <div className="text-xs text-[var(--text-muted)]">© CyberMind 2026</div>
          </div>
        ) : (
          <a
            href="https://github.com/naflashDev"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block"
            title="© CyberMind 2026"
          >
            <img
              src="/CyberMindLogo.webp"
              alt="CyberMind Logo"
              className="w-8 h-auto mx-auto opacity-80 hover:opacity-100 transition-opacity"
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
          </a>
        )}
      </div>
    </aside>
  );
};
