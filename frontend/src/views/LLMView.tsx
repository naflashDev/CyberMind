/**
 * @file LLMView.tsx
 * @author naflashDev
 * @brief Interfaz de chat CyberSentinel IA con soporte de documentos RAG y selección de carpetas.
 */

import React, { useEffect, useState } from 'react';
import { Send, Upload, Folder, Bot, User, FileText } from 'lucide-react';
import { api } from '../services/api';

interface Message {
  role: string;
  content: string;
  created_at?: string;
}

export const LLMView: React.FC = () => {
  const [conversations, setConversations] = useState<Array<{ id: number; title: string }>>([]);
  const [activeConvId, setActiveConvId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [loading, setLoading] = useState(false);

  // Panel de documentos RAG
  const [showDocsPanel, setShowDocsPanel] = useState(false);
  const [folders, setFolders] = useState<{ name: string; path: string }[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string>('');
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  useEffect(() => {
    loadConversations();
    loadFolders();
  }, []);

  const loadConversations = async () => {
    try {
      const convs = await api.getConversations();
      setConversations(convs);
      if (convs.length > 0 && !activeConvId) {
        selectConversation(convs[0].id);
      }
    } catch (e) {
      console.error('Error cargando conversaciones:', e);
    }
  };

  const loadFolders = async () => {
    try {
      const res = await api.getDocFolders();
      if (res.folders) setFolders(res.folders);
    } catch (e) {
      console.error('Error cargando carpetas:', e);
    }
  };

  const selectConversation = async (id: number) => {
    setActiveConvId(id);
    try {
      const msgs = await api.getConversationMessages(id);
      setMessages(msgs);
    } catch {
      setMessages([]);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputPrompt.trim() || loading) return;

    const userMsg = inputPrompt;
    setInputPrompt('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await api.sendLLMMessage({
        prompt: userMsg,
        conversation_id: activeConvId || undefined,
      });
      setMessages((prev) => [...prev, { role: 'assistant', content: res.response }]);
      if (res.conversation_id && res.conversation_id !== activeConvId) {
        setActiveConvId(res.conversation_id);
        loadConversations();
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error comunicando con el modelo: ${(err as Error).message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('file', files[i]);
    }
    if (selectedFolder) {
      formData.append('folder', selectedFolder);
    }
    if (activeConvId) {
      formData.append('conversation_id', activeConvId.toString());
    }

    setUploadStatus('Subiendo e indexando en ChromaDB...');
    try {
      await api.uploadDocument(formData);
      setUploadStatus('¡Documento indexado con éxito!');
      setTimeout(() => setUploadStatus(null), 3000);
      loadFolders();
    } catch (err) {
      setUploadStatus(`Error: ${(err as Error).message}`);
    }
  };

  return (
    <div className="flex h-full gap-4 p-4 overflow-hidden">
      {/* Sidebar de conversaciones */}
      <div className="w-72 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 flex flex-col justify-between shrink-0">
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-sm text-[var(--text-primary)]">Historial</h3>
            <button
              onClick={() => {
                setActiveConvId(null);
                setMessages([]);
              }}
              className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-[var(--brand-primary)] text-white btn-bounce shadow-sm"
            >
              Nueva
            </button>
          </div>

          <div className="space-y-1 overflow-y-auto max-h-[60vh]">
            {conversations.map((c) => (
              <button
                key={c.id}
                onClick={() => selectConversation(c.id)}
                className={`w-full text-left px-3 py-2 rounded-xl text-xs transition-all btn-bounce truncate ${
                  activeConvId === c.id
                    ? 'bg-[var(--brand-primary)]/10 text-[var(--brand-primary)] font-semibold border border-[var(--brand-primary)]/30'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)] hover:text-[var(--text-primary)]'
                }`}
              >
                {c.title || `Conversación #${c.id}`}
              </button>
            ))}
          </div>
        </div>

        {/* Botón Gestión de Documentos RAG */}
        <div className="pt-3 border-t border-[var(--border-subtle)]">
          <button
            onClick={() => setShowDocsPanel(!showDocsPanel)}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20 transition-all btn-bounce"
          >
            <Folder className="w-4 h-4" />
            <span>Documentos RAG</span>
          </button>
        </div>
      </div>

      {/* Área de Chat & Ingestión */}
      <div className="flex-1 flex flex-col bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl overflow-hidden">
        {/* Modal / Panel RAG Dropdown */}
        {showDocsPanel && (
          <div className="p-4 bg-[var(--bg-surface-subtle)] border-b border-[var(--border-subtle)] space-y-3 dropdown-menu-smooth">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[var(--text-primary)] flex items-center gap-2">
                <FileText className="w-4 h-4 text-[var(--brand-primary)]" />
                Ingestión Vectorial RAG (ChromaDB)
              </span>
              <button onClick={() => setShowDocsPanel(false)} className="text-xs text-[var(--text-muted)] hover:text-white">
                ✕
              </button>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={selectedFolder}
                onChange={(e) => setSelectedFolder(e.target.value)}
                className="bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-xl px-3 py-1.5 text-xs text-[var(--text-primary)] focus:outline-none"
              >
                <option value="">Carpeta: (Raíz documents)</option>
                {folders.map((f) => (
                  <option key={f.path} value={f.name}>
                    {f.name}
                  </option>
                ))}
              </select>

              <label className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[var(--brand-primary)] text-white cursor-pointer btn-bounce">
                <Upload className="w-3.5 h-3.5" />
                <span>Subir Documento</span>
                <input type="file" multiple onChange={handleFileUpload} className="hidden" />
              </label>

              {uploadStatus && <span className="text-xs text-emerald-400">{uploadStatus}</span>}
            </div>
          </div>
        )}

        {/* Mensajes del chat */}
        <div className="flex-1 p-6 overflow-y-auto space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center text-[var(--text-muted)]">
              <Bot className="w-12 h-12 text-[var(--brand-primary)]/40 mb-3" />
              <p className="text-sm font-semibold text-[var(--text-primary)]">CyberSentinel IA</p>
              <p className="text-xs max-w-sm mt-1">Consulta vulnerabilidades CVE, analiza código o solicita resúmenes de ciberseguridad con contexto RAG.</p>
            </div>
          ) : (
            messages.map((m, idx) => {
              const isUser = m.role === 'user';
              return (
                <div key={idx} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
                  {!isUser && (
                    <div className="w-8 h-8 rounded-xl bg-[var(--brand-primary)]/10 border border-[var(--brand-primary)]/30 flex items-center justify-center shrink-0">
                      <Bot className="w-4 h-4 text-[var(--brand-primary)]" />
                    </div>
                  )}
                  <div
                    className={`max-w-2xl p-4 rounded-2xl text-xs leading-relaxed ${
                      isUser
                        ? 'bg-[var(--brand-primary)] text-white shadow-md'
                        : 'bg-[var(--bg-surface-subtle)] text-[var(--text-primary)] border border-[var(--border-subtle)]'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{m.content}</p>
                  </div>
                  {isUser && (
                    <div className="w-8 h-8 rounded-xl bg-[var(--border-subtle)] flex items-center justify-center shrink-0">
                      <User className="w-4 h-4 text-[var(--text-secondary)]" />
                    </div>
                  )}
                </div>
              );
            })
          )}
          {loading && (
            <div className="flex gap-3 items-center text-xs text-[var(--text-muted)]">
              <Bot className="w-4 h-4 text-[var(--brand-primary)] animate-pulse" />
              <span>CyberSentinel está analizando...</span>
            </div>
          )}
        </div>

        {/* Input prompt */}
        <form onSubmit={handleSendMessage} className="p-4 border-t border-[var(--border-subtle)] flex gap-3">
          <input
            type="text"
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            placeholder="Pregunta a CyberSentinel (ej: ¿Cuáles son las vulnerabilidades críticas en OpenSSL recientes?)..."
            className="flex-1 bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-xl px-4 py-2.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--brand-primary)]"
          />
          <button
            type="submit"
            disabled={loading || !inputPrompt.trim()}
            className="px-5 py-2.5 rounded-xl bg-[var(--brand-primary)] text-white font-semibold text-xs flex items-center gap-2 hover:bg-[var(--brand-primary-hover)] disabled:opacity-50 transition-all btn-bounce"
          >
            <Send className="w-4 h-4" />
            <span>Enviar</span>
          </button>
        </form>
      </div>
    </div>
  );
};
