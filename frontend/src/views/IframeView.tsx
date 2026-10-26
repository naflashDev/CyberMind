/**
 * @file IframeView.tsx
 * @author naflashDev
 * @brief Componente contenedor de vistas embebidas (OpenSearch Dashboards y Tiny Tiny RSS).
 */

import React, { useState } from 'react';
import { ExternalLink, RefreshCw } from 'lucide-react';

interface IframeViewProps {
  title: string;
  src: string;
  description: string;
}

export const IframeView: React.FC<IframeViewProps> = ({ title, src, description }) => {
  const [loaded, setLoaded] = useState(false);

  return (
    <div className="h-full flex flex-col p-4">
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-[var(--text-primary)]">{title}</h2>
          <p className="text-xs text-[var(--text-muted)]">{description}</p>
        </div>
        <div className="flex items-center gap-3">
          <a
            href={src}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[var(--bg-surface-subtle)] hover:bg-[var(--border-subtle)] text-[var(--brand-primary)] border border-[var(--border-subtle)] btn-bounce"
          >
            <span>Abrir en nueva pestaña</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      <div className="flex-1 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl overflow-hidden relative">
        {!loaded && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-[var(--bg-surface)] z-10 p-6 text-center">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">Integración de {title}</h3>
            <p className="text-xs text-[var(--text-muted)] max-w-md mb-4">
              Asegúrate de que el contenedor correspondiente se encuentra en ejecución en su puerto asignado ({src}).
            </p>
            <button
              onClick={() => setLoaded(true)}
              className="px-5 py-2.5 rounded-xl bg-[var(--brand-primary)] text-white font-semibold text-xs flex items-center gap-2 btn-bounce shadow-md"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Cargar {title}</span>
            </button>
          </div>
        )}
        {loaded && (
          <iframe
            src={src}
            title={title}
            className="w-full h-full border-none"
            sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
          />
        )}
      </div>
    </div>
  );
};
