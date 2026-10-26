/**
 * @file DocsView.tsx
 * @author naflashDev
 * @brief Visor interactivo de la documentación técnica de CyberMind en Markdown.
 */

import React, { useEffect, useState } from 'react';
import { BookOpen, FileText } from 'lucide-react';
import { marked } from 'marked';
import { api } from '../services/api';

export const DocsView: React.FC = () => {
  const [docList, setDocList] = useState<string[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<string>('');
  const [contentHtml, setContentHtml] = useState<string>('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDocs();
  }, []);

  const loadDocs = async () => {
    try {
      const res = await api.getDocsList();
      if (res.files && res.files.length > 0) {
        setDocList(res.files);
        selectDoc(res.files[0]);
      }
    } catch (e) {
      console.error('Error cargando lista de docs:', e);
    }
  };

  const selectDoc = async (filename: string) => {
    setSelectedDoc(filename);
    setLoading(true);
    try {
      const res = await api.getDocContent(filename);
      const parsed = await marked.parse(res.content || '# Sin contenido');
      setContentHtml(parsed);
    } catch {
      setContentHtml('### Error cargando el archivo de documentación.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full gap-4 p-4">
      {/* Lista de Documentos */}
      <div className="w-64 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 shrink-0 flex flex-col">
        <h3 className="font-bold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-[var(--brand-primary)]" />
          Documentos
        </h3>
        <div className="space-y-1 overflow-y-auto flex-1">
          {docList.map((doc) => (
            <button
              key={doc}
              onClick={() => selectDoc(doc)}
              className={`w-full text-left px-3 py-2 rounded-xl text-xs flex items-center gap-2 transition-all btn-bounce ${
                selectedDoc === doc
                  ? 'bg-[var(--brand-primary)] text-white font-semibold'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)] hover:text-[var(--text-primary)]'
              }`}
            >
              <FileText className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate">{doc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Visor de Markdown */}
      <div className="flex-1 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-8 overflow-y-auto">
        {loading ? (
          <div className="text-xs text-[var(--text-muted)]">Cargando documento...</div>
        ) : (
          <div
            className="prose prose-invert max-w-none text-xs leading-relaxed space-y-4"
            dangerouslySetInnerHTML={{ __html: contentHtml }}
          />
        )}
      </div>
    </div>
  );
};
