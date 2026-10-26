/**
 * @file App.tsx
 * @author naflashDev
 * @brief Orquestador central de la interfaz de CyberMind (SPA desacoplada).
 */

import React, { useState } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { Sidebar } from './components/layout/Sidebar';
import type { ActiveTab } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { ServicesView } from './views/ServicesView';
import { LLMView } from './views/LLMView';
import { CodeAnalysisView } from './views/CodeAnalysisView';
import { DocsView } from './views/DocsView';
import { ConfigView } from './views/ConfigView';
import { StatusView } from './views/StatusView';
import { IframeView } from './views/IframeView';

const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('services');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const tabTitles: Record<ActiveTab, string> = {
    services: 'Explorador de Servicios & API',
    llm: 'CyberSentinel IA — Asistente de Inteligencia de Amenazas',
    code: 'Análisis SAST de Código Fuente',
    data: 'OpenSearch Dashboards & Métricas',
    tiny: 'Noticias Tiny Tiny RSS',
    docs: 'Documentación Técnica de CyberMind',
    status: 'Monitor de Estado del Sistema',
    config: 'Configuración & Personalización de Diseño',
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-app)] text-[var(--text-primary)]">
      {/* Barra lateral */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
      />

      {/* Contenedor principal */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          collapsed={sidebarCollapsed}
          setCollapsed={setSidebarCollapsed}
          title={tabTitles[activeTab]}
        />

        <main className="flex-1 overflow-auto bg-[var(--bg-app)]">
          {activeTab === 'services' && <ServicesView />}
          {activeTab === 'llm' && <LLMView />}
          {activeTab === 'code' && <CodeAnalysisView />}
          {activeTab === 'data' && (
            <IframeView
              title="OpenSearch Dashboards"
              src="http://127.0.0.1:5601/"
              description="Visualizador de índices de vulnerabilidades, noticias y clusters de seguridad."
            />
          )}
          {activeTab === 'tiny' && (
            <IframeView
              title="Tiny Tiny RSS"
              src="http://127.0.0.1:8280/tt-rss/"
              description="Gestor y agregador de feeds RSS de fuentes de ciberseguridad y OT/IT."
            />
          )}
          {activeTab === 'docs' && <DocsView />}
          {activeTab === 'status' && <StatusView />}
          {activeTab === 'config' && <ConfigView />}
        </main>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}
