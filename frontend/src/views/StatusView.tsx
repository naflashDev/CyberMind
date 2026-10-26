/**
 * @file StatusView.tsx
 * @author naflashDev
 * @brief Monitor visual del estado del sistema, workers en background e infraestructura.
 */

import React, { useEffect, useState } from 'react';
import { Activity, RefreshCw, CheckCircle2, Cpu } from 'lucide-react';
import { api } from '../services/api';

export const StatusView: React.FC = () => {
  const [statusData, setStatusData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const data = await api.getStatus();
      setStatusData(data);
    } catch (e) {
      console.error('Error cargando estado:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between pb-4 border-b border-[var(--border-subtle)] mb-6">
          <div className="flex items-center gap-3">
            <Activity className="w-6 h-6 text-[var(--brand-primary)]" />
            <div>
              <h2 className="text-lg font-bold text-[var(--text-primary)]">Monitor de Estado del Sistema</h2>
              <p className="text-xs text-[var(--text-secondary)]">Diagnóstico de hilos de scraping, workers asíncronos y servicios</p>
            </div>
          </div>
          <button
            onClick={loadStatus}
            disabled={loading}
            className="px-4 py-2 rounded-xl border border-[var(--border-subtle)] hover:bg-[var(--bg-surface-subtle)] text-xs font-semibold text-[var(--text-primary)] flex items-center gap-2 btn-bounce"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Actualizar</span>
          </button>
        </div>

        {/* Tarjetas resumen */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="p-4 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)]">
            <span className="text-xs text-[var(--text-muted)] block mb-1">Infraestructura</span>
            <span className="text-sm font-bold text-emerald-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              Operativa
            </span>
          </div>

          <div className="p-4 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)]">
            <span className="text-xs text-[var(--text-muted)] block mb-1">Backend FastAPI</span>
            <span className="text-sm font-bold text-[var(--brand-primary)] flex items-center gap-1.5">
              <Cpu className="w-4 h-4" />
              Online (Puerto 8000)
            </span>
          </div>

          <div className="p-4 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)]">
            <span className="text-xs text-[var(--text-muted)] block mb-1">Vectorstore RAG</span>
            <span className="text-sm font-bold text-cyan-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              ChromaDB Persistente
            </span>
          </div>
        </div>

        {/* JSON Dump crudo */}
        <div className="bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-xl p-4 overflow-hidden">
          <span className="text-xs font-mono text-[var(--text-muted)] block mb-2">Metadatos de Estado:</span>
          <pre className="font-mono text-xs text-[var(--text-secondary)] overflow-auto max-h-96">
            {statusData ? JSON.stringify(statusData, null, 2) : 'Cargando estado...'}
          </pre>
        </div>
      </div>
    </div>
  );
};
