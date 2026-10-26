/**
 * @file Sidebar.tsx
 * @author naflashDev
 * @brief Barra de navegación principal con iconos semánticos Lucide y diseño de alta densidad.
 * @details Conecta con las vistas principales del sistema y ofrece indicador de estado en tiempo real.
 */

import React from 'react';
import {
  Zap,
  BarChart2,
  Newspaper,
  Bot,
  BookOpen,
  Settings,
  Shield,
  Activity,
  Code,
} from 'lucide-react';

export type ActiveTab = 'services' | 'data' | 'tiny' | 'llm' | 'code' | 'docs' | 'config' | 'status';

interface SidebarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  collapsed,
}) => {
  const navItems = [
    { id: 'services' as ActiveTab, label: 'Services API', icon: Zap },
    { id: 'llm' as ActiveTab, label: 'CyberSentinel IA', icon: Bot },
    { id: 'code' as ActiveTab, label: 'Análisis de Código', icon: Code },
    { id: 'data' as ActiveTab, label: 'OpenSearch Datos', icon: BarChart2 },
    { id: 'tiny' as ActiveTab, label: 'Noticias Tiny', icon: Newspaper },
    { id: 'docs' as ActiveTab, label: 'Documentación', icon: BookOpen },
    { id: 'status' as ActiveTab, label: 'Estado Sistema', icon: Activity },
    { id: 'config' as ActiveTab, label: 'Configuración', icon: Settings },
  ];

  return (
    <aside
      className={`h-screen flex flex-col justify-between border-r border-[var(--border-subtle)] bg-[var(--bg-surface)] transition-all duration-300 z-30 select-none ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Cabecera Sidebar */}
      <div>
        <div className="p-4 flex items-center justify-between border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-[var(--brand-primary)]/10 border border-[var(--brand-primary)]/30 flex items-center justify-center shrink-0">
              <Shield className="w-5 h-5 text-[var(--brand-primary)]" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-bold text-base tracking-tight text-[var(--text-primary)]">CyberMind</span>
                <span className="text-[10px] tracking-wider uppercase text-[var(--brand-primary)] font-semibold">Security Suite</span>
              </div>
            )}
          </div>
        </div>

        {/* Navegación */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl font-medium text-sm transition-all btn-bounce ${
                  isActive
                    ? 'bg-[var(--brand-primary)] text-white shadow-lg shadow-[var(--brand-primary)]/20 font-semibold'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)] hover:text-[var(--text-primary)]'
                }`}
                title={item.label}
              >
                <Icon className={`w-5 h-5 shrink-0 ${isActive ? 'text-white' : 'text-[var(--text-muted)]'}`} />
                {!collapsed && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Sidebar */}
      <div className="p-4 border-t border-[var(--border-subtle)]">
        {!collapsed && (
          <div className="text-center">
            <img
              src="/CyberMindLogo.webp"
              alt="CyberMind Logo"
              className="w-20 h-auto mx-auto mb-2 opacity-80 hover:opacity-100 transition-opacity"
              onError={(e) => {
                // Fallback si no está presente la imagen webp
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
            <p className="text-[11px] text-[var(--text-muted)]">© CyberMind 2026</p>
          </div>
        )}
      </div>
    </aside>
  );
};
