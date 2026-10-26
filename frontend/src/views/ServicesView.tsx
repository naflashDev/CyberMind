/**
 * @file ServicesView.tsx
 * @author naflashDev
 * @brief Interfaz para explorar y ejecutar servicios y controladores FastAPI (FastAPI Explorer).
 */

import React, { useState } from 'react';
import { Zap, Play, Terminal } from 'lucide-react';
import { api } from '../services/api';

export const ServicesView: React.FC = () => {
  const [selectedService, setSelectedService] = useState<'network' | 'range' | 'health'>('network');
  const [targetHost, setTargetHost] = useState('127.0.0.1');
  const [targetPorts, setTargetPorts] = useState('80, 443, 8000, 9200');
  const [rangeCidr, setRangeCidr] = useState('192.168.1.0/28');
  const [useNmap, setUseNmap] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [responseOutput, setResponseOutput] = useState<string | null>(null);

  const handleExecute = async () => {
    setExecuting(true);
    setResponseOutput('Ejecutando operación...');
    try {
      if (selectedService === 'network') {
        const parsedPorts = targetPorts
          .split(',')
          .map((p) => parseInt(p.trim()))
          .filter((n) => !isNaN(n));
        const res = await api.scanNetworkPort({
          host: targetHost,
          ports: parsedPorts.length > 0 ? parsedPorts : undefined,
          use_nmap: useNmap,
        });
        setResponseOutput(JSON.stringify(res, null, 2));
      } else if (selectedService === 'range') {
        const res = await api.scanNetworkRange({
          cidr: rangeCidr,
          use_nmap: useNmap,
        });
        setResponseOutput(JSON.stringify(res, null, 2));
      } else if (selectedService === 'health') {
        const res = await api.getHealth();
        setResponseOutput(JSON.stringify(res, null, 2));
      }
    } catch (e) {
      setResponseOutput(`Error: ${(e as Error).message}`);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="flex h-full gap-4 p-4">
      {/* Menú de operaciones */}
      <div className="w-72 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 shrink-0 space-y-2">
        <h3 className="font-bold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
          <Zap className="w-4 h-4 text-[var(--brand-primary)]" />
          Servicios Disponibles
        </h3>
        <button
          onClick={() => setSelectedService('network')}
          className={`w-full text-left px-3 py-2.5 rounded-xl text-xs font-semibold transition-all btn-bounce ${
            selectedService === 'network'
              ? 'bg-[var(--brand-primary)] text-white'
              : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)] hover:text-[var(--text-primary)]'
          }`}
        >
          Network: Port Scan (Nmap)
        </button>
        <button
          onClick={() => setSelectedService('range')}
          className={`w-full text-left px-3 py-2.5 rounded-xl text-xs font-semibold transition-all btn-bounce ${
            selectedService === 'range'
              ? 'bg-[var(--brand-primary)] text-white'
              : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)] hover:text-[var(--text-primary)]'
          }`}
        >
          Network: Range Scan (CIDR)
        </button>
        <button
          onClick={() => setSelectedService('health')}
          className={`w-full text-left px-3 py-2.5 rounded-xl text-xs font-semibold transition-all btn-bounce ${
            selectedService === 'health'
              ? 'bg-[var(--brand-primary)] text-white'
              : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)] hover:text-[var(--text-primary)]'
          }`}
        >
          System Health Check
        </button>
      </div>

      {/* Formulario y Consola */}
      <div className="flex-1 flex flex-col bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 overflow-hidden">
        <div className="mb-6 space-y-4">
          <h2 className="text-base font-bold text-[var(--text-primary)]">
            {selectedService === 'network' && 'Escaneo de Puertos y Detección de Servicios'}
            {selectedService === 'range' && 'Escaneo de Rango de Red (CIDR)'}
            {selectedService === 'health' && 'Comprobación de Salud del Backend'}
          </h2>

          {selectedService === 'network' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-[var(--text-secondary)] mb-1">Host Destino</label>
                <input
                  type="text"
                  value={targetHost}
                  onChange={(e) => setTargetHost(e.target.value)}
                  className="w-full bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-xl px-3 py-2 text-xs text-[var(--text-primary)]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--text-secondary)] mb-1">Puertos (separados por coma)</label>
                <input
                  type="text"
                  value={targetPorts}
                  onChange={(e) => setTargetPorts(e.target.value)}
                  className="w-full bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-xl px-3 py-2 text-xs text-[var(--text-primary)]"
                />
              </div>
            </div>
          )}

          {selectedService === 'range' && (
            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)] mb-1">Rango CIDR</label>
              <input
                type="text"
                value={rangeCidr}
                onChange={(e) => setRangeCidr(e.target.value)}
                className="w-full bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-xl px-3 py-2 text-xs text-[var(--text-primary)]"
              />
            </div>
          )}

          {selectedService !== 'health' && (
            <label className="flex items-center gap-2 text-xs font-medium text-[var(--text-secondary)] cursor-pointer">
              <input
                type="checkbox"
                checked={useNmap}
                onChange={(e) => setUseNmap(e.target.checked)}
                className="rounded text-[var(--brand-primary)]"
              />
              <span>Usar escáner Nmap integrado</span>
            </label>
          )}

          <button
            onClick={handleExecute}
            disabled={executing}
            className="px-5 py-2.5 rounded-xl bg-[var(--brand-primary)] text-white font-semibold text-xs flex items-center gap-2 hover:bg-[var(--brand-primary-hover)] disabled:opacity-50 transition-all btn-bounce shadow-md"
          >
            <Play className="w-4 h-4" />
            <span>{executing ? 'Ejecutando...' : 'Ejecutar Petición'}</span>
          </button>
        </div>

        {/* Consola de Salida */}
        <div className="flex-1 flex flex-col bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-xl p-4 overflow-hidden">
          <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-muted)] mb-2">
            <Terminal className="w-4 h-4 text-[var(--brand-primary)]" />
            <span>Respuesta JSON del Endpoint</span>
          </div>
          <pre className="flex-1 overflow-auto font-mono text-xs text-emerald-400 leading-relaxed whitespace-pre-wrap">
            {responseOutput || 'Seleccione una operación y pulse "Ejecutar Petición" para inspeccionar la respuesta.'}
          </pre>
        </div>
      </div>
    </div>
  );
};
