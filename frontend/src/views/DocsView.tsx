/**
 * @file DocsView.tsx
 * @author naflashDev
 * @brief Interactive Markdown documentation viewer replicating view-docs from index.html and ui.js with modern Lucide icons.
 * @details Orders README.md first and Indice.md second, applies friendly names, and intercepts internal .md links.
 */

import React, { useEffect, useState, useRef, useCallback } from 'react';
import { BookOpen, FileText } from 'lucide-react';
import { marked } from 'marked';
import { api } from '../services/api';

const DOCS_FRIENDLY_NAMES: Record<string, string> = {
  'README.md': 'Introducción (README)',
  'Indice.md': 'Índice general',
  'home.md': 'Resumen y objetivo',
  'api_endpoints.md': 'API Endpoints',
  'llm.md': 'LLM (IA integrada)',
  'instalacion_dependencias.md': 'Instalación dependencias',
  'opensearch_install.md': 'Instalación OpenSearch',
  'tiny_rss_install.md': 'Instalación Tiny RSS',
  'task.md': 'Tareas y operaciones',
  'ChangeLog.md': 'Registro de cambios',
};

/**
 * @brief Get a friendly display name for a documentation file.
 */
function getFriendlyName(filename: string): string {
  return (
    DOCS_FRIENDLY_NAMES[filename] ||
    filename
      .replace('.md', '')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase())
  );
}

interface DocsViewProps {
  isActive?: boolean;
}

export const DocsView: React.FC<DocsViewProps> = ({ isActive }) => {
  const [orderedDocs, setOrderedDocs] = useState<string[]>(['README.md']);
  const [selectedDoc, setSelectedDoc] = useState<string>('README.md');
  const [contentHtml, setContentHtml] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const contentRef = useRef<HTMLDivElement>(null);

  /**
   * @brief Load and render a documentation file's Markdown content.
   */
  const selectDoc = useCallback(async (filename: string) => {
    setSelectedDoc(filename);
    setLoading(true);
    setErrorMsg(null);
    try {
      const rawText =
        filename === 'README.md'
          ? await api.getDocReadme()
          : await api.getDocFile(filename);
      const parsed = await marked.parse(rawText || '');
      setContentHtml(parsed);
    } catch {
      setErrorMsg('Error cargando documento');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * @brief Fetch the documentation file list and build the ordered sidebar list.
   */
  const loadDocsList = useCallback(async () => {
    try {
      const files = await api.getDocsList();
      const fileList = Array.isArray(files) ? files : [];
      const list: string[] = ['README.md'];
      if (fileList.includes('Indice.md')) {
        list.push('Indice.md');
      }
      fileList
        .filter((f) => f !== 'README.md' && f !== 'Indice.md')
        .forEach((f) => list.push(f));
      setOrderedDocs(list);
    } catch (e) {
      console.error('Error cargando lista de documentos:', e);
    }
  }, []);

  useEffect(() => {
    loadDocsList();
    selectDoc('README.md');
  }, [loadDocsList, selectDoc]);

  useEffect(() => {
    if (isActive && !contentHtml && !loading) {
      selectDoc('README.md');
    }
  }, [isActive, contentHtml, loading, selectDoc]);

  /**
   * @brief Intercept clicks on internal .md links inside the rendered documentation.
   */
  const handleContentClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = (e.target as HTMLElement).closest('a');
    if (!target) return;
    const href = target.getAttribute('href');
    if (!href) return;
    if (
      href.endsWith('.md') ||
      href.startsWith('./') ||
      href.startsWith('../')
    ) {
      const file = href.split('/').pop()?.replace(/^\.?\/?/, '') || '';
      if (file.endsWith('.md')) {
        e.preventDefault();
        selectDoc(file);
      }
    }
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left: Documentation list pane */}
      <div className="docs-list-pane w-64 bg-[var(--bg-surface)] border-r border-[var(--border-subtle)] p-4 overflow-y-auto shrink-0">
        <h3 className="font-bold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-[var(--brand-primary)]" />
          <span>Documentos</span>
        </h3>

        <ul id="docs-list" className="space-y-1 list-none p-0 m-0">
          {orderedDocs.map((doc) => {
            const isSelected = selectedDoc === doc;
            return (
              <li key={doc}>
                <button
                  type="button"
                  onClick={() => selectDoc(doc)}
                  className={`doc-btn w-full text-left px-3 py-2 rounded-xl text-xs flex items-center gap-2 transition-all btn-bounce ${
                    isSelected
                      ? 'active bg-[var(--brand-primary)] text-white font-semibold shadow-sm'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)] hover:text-[var(--text-primary)]'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate">{getFriendlyName(doc)}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Right: Documentation content pane */}
      <div className="docs-content-pane flex-1 p-6 overflow-y-auto bg-[var(--bg-app)]">
        <div
          id="docs-content"
          ref={contentRef}
          onClick={handleContentClick}
          className="max-w-4xl mx-auto bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-8 min-h-[80vh] shadow-xl overflow-x-auto break-words"
        >
          {loading ? (
            <div className="text-xs text-[var(--text-muted)]">Cargando...</div>
          ) : errorMsg ? (
            <div className="text-xs text-rose-400">{errorMsg}</div>
          ) : (
            <div
              className="prose prose-invert max-w-none text-sm leading-relaxed space-y-4"
              dangerouslySetInnerHTML={{ __html: contentHtml }}
            />
          )}
        </div>
      </div>
    </div>
  );
};
