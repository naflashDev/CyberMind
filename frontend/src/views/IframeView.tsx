/**
 * @file IframeView.tsx
 * @author naflashDev
 * @brief Embedded iframe container replicating the lazy-loading behavior of view-datos and view-tiny in index.html & ui.js.
 */

import React, { useState, useEffect } from 'react';
import { ExternalLink, RefreshCw } from 'lucide-react';

interface IframeViewProps {
  title: string;
  buttonLabel: string;
  src: string;
  isActive?: boolean;
}

export const IframeView: React.FC<IframeViewProps> = ({
  title,
  buttonLabel,
  src,
  isActive,
}) => {
  const [loaded, setLoaded] = useState(false);

  // Auto-load iframe on first activation just like ensureFrameLoaded(viewName) in ui.js
  useEffect(() => {
    if (isActive && !loaded) {
      setLoaded(true);
    }
  }, [isActive, loaded]);

  return (
    <div className="h-full w-full flex flex-col overflow-hidden">
      <div className="px-4 py-2 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)] flex items-center justify-between shrink-0">
        <span className="text-xs font-semibold text-[var(--text-secondary)]">
          {title} — <code className="text-[var(--brand-primary)]">{src}</code>
        </span>
        <a
          href={src}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[var(--bg-surface-subtle)] hover:bg-[var(--border-subtle)] text-[var(--brand-primary)] border border-[var(--border-subtle)] transition-all"
        >
          <span>Abrir en pestaña nueva</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>

      <div
        className="iframe-placeholder flex-1 w-full h-full flex items-center justify-center bg-[var(--bg-app)] relative"
        data-src={src}
        data-loaded={loaded ? '1' : '0'}
      >
        {!loaded ? (
          <button
            type="button"
            onClick={() => setLoaded(true)}
            className="load-iframe-btn px-5 py-2.5 rounded-xl bg-[var(--brand-primary)] text-white font-semibold text-xs flex items-center gap-2 btn-bounce shadow-md"
          >
            <RefreshCw className="w-4 h-4" />
            <span>{buttonLabel}</span>
          </button>
        ) : (
          <iframe
            src={src}
            title={title}
            loading="eager"
            className="embed-frame w-full h-full border-0 bg-white"
            sandbox="allow-scripts allow-forms allow-same-origin allow-popups"
          />
        )}
      </div>
    </div>
  );
};
