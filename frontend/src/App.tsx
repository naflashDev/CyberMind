/**
 * @file App.tsx
 * @author naflashDev
 * @brief Central orchestrator of the CyberMind SPA replicating index.html and ui.js architecture.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { Sidebar } from './components/layout/Sidebar';
import type { ActiveTab } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { ServicesView } from './views/ServicesView';
import { LLMView } from './views/LLMView';
import { DocsView } from './views/DocsView';
import { ConfigView } from './views/ConfigView';
import { IframeView } from './views/IframeView';
import { api } from './services/api';

const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('fastapi');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [useOllama, setUseOllama] = useState<boolean>(true);

  /**
   * @brief Check /config to determine if use_ollama is enabled and update CyberSentinel IA visibility.
   */
  const updateCyberSentinelVisibility = useCallback(async () => {
    try {
      const data = await api.getConfig();
      let enabled = false;
      for (const file of data.files || []) {
        for (const p of file.params || []) {
          if (p.key === 'use_ollama') {
            enabled = String(p.value).toLowerCase() === 'true';
          }
        }
      }
      setUseOllama(enabled);
      if (!enabled && activeTab === 'llm') {
        setActiveTab('fastapi');
      }
    } catch {
      // Show by default if config cannot be fetched
      setUseOllama(true);
    }
  }, [activeTab]);

  useEffect(() => {
    updateCyberSentinelVisibility();
  }, [updateCyberSentinelVisibility]);

  const tabTitles: Record<ActiveTab, string> = {
    fastapi: 'Services — Operaciones de los Controllers',
    datos: 'Datos — OpenSearch Dashboards',
    tiny: 'Noticias Tiny — Tiny Tiny RSS',
    llm: 'CyberSentinel IA — Asistente Local (Ollama)',
    docs: 'Documentación del Proyecto',
    config: 'Configuración del Sistema',
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-app)] text-[var(--text-primary)]">
      {/* Main Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
        useOllama={useOllama}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden main">
        <Header
          collapsed={sidebarCollapsed}
          setCollapsed={setSidebarCollapsed}
          title={tabTitles[activeTab]}
        />

        <main className="flex-1 overflow-hidden bg-[var(--bg-app)] main-content relative">
          {/* Keep views mounted to preserve form caches, running requests and loaded iframes */}
          <div
            id="view-fastapi"
            className={`view h-full w-full ${activeTab === 'fastapi' ? 'flex flex-col active' : 'hidden'}`}
          >
            <ServicesView />
          </div>

          <div
            id="view-datos"
            className={`view h-full w-full ${activeTab === 'datos' ? 'flex flex-col active' : 'hidden'}`}
          >
            <IframeView
              title="OpenSearch Dashboards"
              buttonLabel="Cargar OpenSearch Dashboards"
              src="http://127.0.0.1:5601/"
              isActive={activeTab === 'datos'}
            />
          </div>

          <div
            id="view-tiny"
            className={`view h-full w-full ${activeTab === 'tiny' ? 'flex flex-col active' : 'hidden'}`}
          >
            <IframeView
              title="Tiny Tiny RSS"
              buttonLabel="Cargar Tiny Tiny RSS"
              src="http://127.0.0.1:8282/tt-rss/"
              isActive={activeTab === 'tiny'}
            />
          </div>

          {useOllama && (
            <div
              id="view-llm"
              className={`view h-full w-full ${activeTab === 'llm' ? 'flex flex-col active' : 'hidden'}`}
            >
              <LLMView isActive={activeTab === 'llm'} />
            </div>
          )}

          <div
            id="view-docs"
            className={`view h-full w-full ${activeTab === 'docs' ? 'flex flex-col active' : 'hidden'}`}
          >
            <DocsView isActive={activeTab === 'docs'} />
          </div>

          <div
            id="view-config"
            className={`view h-full w-full ${activeTab === 'config' ? 'flex flex-col active' : 'hidden'}`}
          >
            <ConfigView
              isActive={activeTab === 'config'}
              onConfigSaved={updateCyberSentinelVisibility}
            />
          </div>
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
