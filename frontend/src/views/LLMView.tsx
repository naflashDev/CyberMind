/**
 * @file LLMView.tsx
 * @author naflashDev
 * @brief Exact functional replication of the CyberSentinel IA view (view-llm) from index.html and ui.js with modern Lucide icons.
 * @details Supports conversation management (create, select, delete on hover), local Ollama queries via /llm/query,
 *          and the RAG Documents upload panel with folder selection, path display, and drag & drop.
 */

import React, { useEffect, useState, useRef, useCallback } from 'react';
import {
  Send,
  Upload,
  Folder,
  Bot,
  Trash2,
  Plus,
  X,
  FileText,
} from 'lucide-react';
import { marked } from 'marked';
import {
  api,
  type ConversationSummary,
  type ConversationMessage,
} from '../services/api';

interface LLMViewProps {
  isActive?: boolean;
}

export const LLMView: React.FC<LLMViewProps> = ({ isActive }) => {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loadingConvs, setLoadingConvs] = useState(false);
  const [convError, setConvError] = useState<string | null>(null);

  const [selectedConvId, setSelectedConvId] = useState<number | null>(null);
  const [selectedConvTitle, setSelectedConvTitle] = useState<string>('');
  const [messages, setMessages] = useState<ConversationMessage[]>([]);

  const [inputPrompt, setInputPrompt] = useState('');
  const [sending, setSending] = useState(false);

  // Documents panel state
  const [showDocsPanel, setShowDocsPanel] = useState(false);
  const [folders, setFolders] = useState<{ name: string; path: string }[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string>(() => {
    try {
      return window.localStorage.getItem('docs_selected_folder') || '';
    } catch {
      return '';
    }
  });
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadingDocs, setUploadingDocs] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string>('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  /**
   * @brief Fetch conversation list without auto-selecting any existing conversation.
   */
  const fetchConversations = useCallback(async () => {
    setLoadingConvs(true);
    setConvError(null);
    try {
      const data = await api.getConversations();
      setConversations(Array.isArray(data) ? data : []);
    } catch {
      setConvError('No se pudieron cargar conversaciones');
    } finally {
      setLoadingConvs(false);
    }
  }, []);

  useEffect(() => {
    if (isActive) {
      fetchConversations();
    }
  }, [isActive, fetchConversations]);

  /**
   * @brief Load folders from /documents/folders when opening the Documents panel.
   */
  const loadDocumentFolders = async () => {
    try {
      const data = await api.getDocFolders();
      setFolders(Array.isArray(data?.folders) ? data.folders : []);
    } catch (e) {
      console.error('[UI] loadDocumentFolders error', e);
    }
  };

  /**
   * @brief Compute the displayed selected folder path exactly like updateSelectedPath() in ui.js.
   */
  const getSelectedFolderPath = () => {
    if (!selectedFolder) return 'data/documents/default';
    const found = folders.find((f) => f.name === selectedFolder);
    return found?.path || `data/documents/${selectedFolder}`;
  };

  const handleFolderChange = (val: string) => {
    setSelectedFolder(val);
    try {
      window.localStorage.setItem('docs_selected_folder', val || '');
    } catch {
      // Ignore storage errors
    }
  };

  /**
   * @brief Select a conversation by ID and load its messages.
   */
  const selectConversation = async (id: number) => {
    setSelectedConvId(id);
    try {
      const conv = await api.getConversation(id);
      const msgs = Array.isArray(conv.messages) ? conv.messages : [];
      setMessages(msgs);

      if (conv.title && String(conv.title).trim()) {
        setSelectedConvTitle(`— ${conv.title}`);
      } else if (msgs.length > 0 && msgs[0]?.text) {
        const firstLine = String(msgs[0].text).split(/\r?\n/)[0].trim();
        const words = firstLine.split(/\s+/).slice(0, 8).join(' ');
        const short = words.length > 60 ? `${words.slice(0, 57)}...` : words;
        setSelectedConvTitle(short ? `— ${short}` : '');
      } else {
        setSelectedConvTitle('');
      }
    } catch (e) {
      window.alert(`Error cargando la conversación: ${(e as Error).message}`);
    }
  };

  /**
   * @brief Create a new conversation with optional title and select it.
   */
  const createConversation = async (pTitle?: string): Promise<number | null> => {
    try {
      const titleToSend =
        typeof pTitle === 'string' && pTitle.trim() ? pTitle.trim() : 'Chat';
      const conv = await api.createConversation(titleToSend);
      setSelectedConvId(conv.id);
      await fetchConversations();
      await selectConversation(conv.id);
      return conv.id;
    } catch {
      window.alert('Error creando conversación');
      return null;
    }
  };

  /**
   * @brief Delete a conversation after user confirmation.
   */
  const handleDeleteConversation = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm('¿Eliminar conversación? Esta acción no se puede deshacer.')) {
      return;
    }
    try {
      await api.deleteConversation(id);
      if (selectedConvId === id) {
        setSelectedConvId(null);
        setSelectedConvTitle('');
        setMessages([]);
      }
      setConversations((prev) => prev.filter((c) => c.id !== id));
    } catch {
      window.alert('Error eliminando la conversación');
    }
  };

  /**
   * @brief Send user prompt to /llm/query, creating a conversation first if needed.
   */
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const text = inputPrompt.trim();
    if (!text || sending) return;

    setSending(true);
    try {
      let targetConvId = selectedConvId;
      if (targetConvId === null) {
        const firstLine = text.split(/\r?\n/)[0].trim();
        const words = firstLine.split(/\s+/).slice(0, 8).join(' ');
        const short = words.length > 60 ? `${words.slice(0, 57)}...` : words;
        targetConvId = await createConversation(short || 'Chat');
      }

      const userMsg: ConversationMessage = {
        role: 'user',
        text,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInputPrompt('');

      const data = await api.queryLLM({
        prompt: text,
        conversation_id: targetConvId,
        top_k: 5,
      });

      const assistantText =
        data && (data.response || data.result)
          ? String(data.response || data.result)
          : 'Sin respuesta del LLM';

      const assistantMsg: ConversationMessage = {
        role: 'assistant',
        text: assistantText,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      window.alert(`Error enviando mensaje: ${(err as Error).message}`);
    } finally {
      setSending(false);
    }
  };

  /**
   * @brief Upload selected RAG documents to /documents/upload.
   */
  const handleUploadDocuments = async () => {
    setUploadStatus('');
    if (!selectedFiles.length) {
      setUploadStatus('Selecciona un archivo para subir.');
      return;
    }

    const form = new FormData();
    selectedFiles.forEach((f) => form.append('file', f));
    if (selectedFolder.trim()) {
      form.append('folder', selectedFolder.trim());
    }
    if (selectedConvId) {
      form.append('conversation_id', String(selectedConvId));
    }

    setUploadingDocs(true);
    try {
      const data = await api.uploadDocuments(form);
      const msg =
        data && Array.isArray(data.results)
          ? data.results.map((r) => r.message || r.file || r.doc_id).join('; ')
          : 'OK';
      setUploadStatus(`Subido: ${msg}`);
      setTimeout(() => {
        setShowDocsPanel(false);
        setSelectedFiles([]);
        setUploadStatus('');
        if (fileInputRef.current) fileInputRef.current.value = '';
      }, 900);
    } catch {
      setUploadStatus('Error subiendo archivo.');
    } finally {
      setUploadingDocs(false);
    }
  };

  return (
    <div id="llm-panel" className="flex h-full gap-4 p-4 overflow-hidden">
      {/* Left: Conversations List */}
      <div className="conv-list w-72 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 flex flex-col justify-between shrink-0 h-full">
        <div className="flex flex-col flex-1 min-h-0">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-sm text-[var(--text-primary)] m-0">
              Conversaciones
            </h3>
            <button
              id="btn-new-conv"
              type="button"
              onClick={() => createConversation()}
              title="Nueva conversación"
              className="px-3 py-1.5 rounded-xl bg-[var(--brand-primary)] text-white text-xs font-semibold flex items-center gap-1 btn-bounce shadow-sm"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Nueva</span>
            </button>
          </div>

          <div id="conv-list" className="flex-1 overflow-y-auto space-y-1.5 min-h-0 pr-1">
            {loadingConvs ? (
              <div className="text-xs text-[var(--text-muted)]">Cargando...</div>
            ) : convError ? (
              <div className="text-xs text-rose-400">{convError}</div>
            ) : conversations.length === 0 ? (
              <div className="text-xs text-[var(--text-muted)]">
                No hay conversaciones. Crea una nueva.
              </div>
            ) : (
              conversations.map((c) => {
                const isSelected = selectedConvId === c.id;
                return (
                  <div
                    key={c.id}
                    className="conv-row group flex items-center gap-1.5"
                  >
                    <button
                      type="button"
                      data-conv-id={String(c.id)}
                      onClick={() => selectConversation(c.id)}
                      className={`conv-item flex-1 text-left p-2.5 rounded-xl transition-all ${
                        isSelected
                          ? 'bg-[var(--brand-primary)]/15 border border-[var(--brand-primary)]/40 text-[var(--text-primary)]'
                          : 'hover:bg-[var(--bg-surface-subtle)] text-[var(--text-secondary)]'
                      }`}
                    >
                      <div className="font-bold text-xs truncate text-[var(--text-primary)]">
                        {c.title || `Conversation ${c.id}`}
                      </div>
                      <div className="text-[11px] text-[var(--text-muted)] mt-0.5">
                        {c.created_at ? new Date(c.created_at).toLocaleString() : ''}
                      </div>
                    </button>

                    <button
                      type="button"
                      title="Eliminar conversación"
                      onClick={(e) => handleDeleteConversation(e, c.id)}
                      className="conv-delete-btn hidden group-hover:flex items-center justify-center w-8 h-8 rounded-lg bg-rose-600 hover:bg-rose-500 text-white shrink-0 transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Retention notice & Documents button */}
        <div className="pt-3 mt-2 border-t border-[var(--border-subtle)] space-y-2.5">
          <div className="text-[11px] text-[var(--text-muted)] text-center">
            Las conversaciones se eliminarán automáticamente a la semana.
          </div>
          <button
            id="btn-manage-docs"
            type="button"
            title="Gestionar documentos"
            onClick={async () => {
              const willShow = !showDocsPanel;
              if (willShow) {
                await loadDocumentFolders();
              }
              setShowDocsPanel(willShow);
            }}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/25 transition-all btn-bounce"
          >
            <Folder className="w-4 h-4" />
            <span>Documentos</span>
          </button>
        </div>
      </div>

      {/* Right: Chat & Documents Panel */}
      <div className="conv-chat flex-1 flex flex-col bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 overflow-hidden">
        <div className="mb-2">
          <div className="flex items-center gap-3">
            <h2 className="font-bold text-base text-[var(--text-primary)] m-0 flex items-center gap-2">
              <Bot className="w-5 h-5 text-[var(--brand-primary)]" />
              <span>CyberSentinel IA</span>
            </h2>
            <div id="selected-conv-title" className="text-xs text-[var(--text-muted)]">
              {selectedConvTitle}
            </div>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Interactúa con el modelo local (Ollama) y revisa el historial.
          </p>
        </div>

        {/* Messages container */}
        <div
          id="llm-messages"
          className="flex-1 overflow-y-auto bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-xl p-4 space-y-3"
        >
          {messages.map((m, idx) => {
            const isUser = m.role === 'user';
            const parsedHtml = !isUser
              ? (marked.parse(m.text || '') as string)
              : null;

            return (
              <div
                key={idx}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                    isUser
                      ? 'user-message max-w-[50%] bg-[var(--brand-primary)] text-white text-right whitespace-pre-wrap break-words shadow-md'
                      : 'bot-message max-w-[80%] bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] text-[var(--text-primary)] text-left'
                  }`}
                >
                  {isUser ? (
                    <div>{m.text}</div>
                  ) : (
                    <div
                      className="prose prose-invert max-w-none text-xs"
                      dangerouslySetInnerHTML={{ __html: parsedHtml || '' }}
                    />
                  )}
                  {m.timestamp && (
                    <div
                      className={`text-[10px] mt-1.5 opacity-75 ${
                        isUser ? 'text-right' : 'text-left text-[var(--text-muted)]'
                      }`}
                    >
                      {new Date(m.timestamp).toLocaleString()}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* Documents panel (hidden by default) */}
        {showDocsPanel && (
          <div
            id="documents-panel"
            className="mt-3 p-4 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-3"
          >
            <h3 className="font-bold text-xs text-[var(--text-primary)] flex items-center gap-2 m-0">
              <FileText className="w-4 h-4 text-[var(--brand-primary)]" />
              <span>Documentos para el LLM</span>
            </h3>

            <div className="flex items-center gap-3">
              <label className="text-xs text-[var(--text-secondary)] w-24">Carpeta:</label>
              <select
                id="docs-folder-select"
                value={selectedFolder}
                onChange={(e) => handleFolderChange(e.target.value)}
                className="flex-1 px-3 py-2 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-app)] text-xs text-[var(--text-primary)]"
              >
                <option value="">(default)</option>
                {folders.map((f) => (
                  <option key={f.name} value={f.name} data-path={f.path}>
                    {f.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="text-xs text-sky-400">
              Ruta seleccionada:{' '}
              <span id="docs-selected-path" className="text-[var(--text-secondary)] font-mono">
                {getSelectedFolderPath()}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <label className="text-xs text-[var(--text-secondary)] w-24">Archivo:</label>
              <div
                id="docs-dropzone"
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    setSelectedFiles(Array.from(e.dataTransfer.files));
                  }
                }}
                className="flex-1 p-3.5 rounded-xl border-2 border-dashed border-[var(--border-subtle)] hover:border-[var(--brand-primary)] bg-[var(--bg-app)] text-xs text-[var(--text-secondary)] flex items-center justify-center cursor-pointer min-h-[56px] transition-all"
              >
                {selectedFiles.length > 0
                  ? selectedFiles.map((f) => f.name).join(', ')
                  : 'Arrastra y suelta aquí o haz clic para seleccionar'}
              </div>
              <input
                ref={fileInputRef}
                id="docs-file-input"
                type="file"
                multiple
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    setSelectedFiles(Array.from(e.target.files));
                  } else {
                    setSelectedFiles([]);
                  }
                }}
              />
            </div>

            <div className="flex items-center gap-2.5">
              <button
                id="docs-upload-btn"
                type="button"
                disabled={uploadingDocs}
                onClick={handleUploadDocuments}
                className="px-3.5 py-2 rounded-xl bg-[var(--brand-primary)] text-white text-xs font-semibold flex items-center gap-1.5 btn-bounce disabled:opacity-50"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>{uploadingDocs ? 'Subiendo...' : 'Subir'}</span>
              </button>
              <button
                id="docs-close-btn"
                type="button"
                onClick={() => setShowDocsPanel(false)}
                className="px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center gap-1.5 btn-bounce"
              >
                <X className="w-3.5 h-3.5" />
                <span>Cerrar</span>
              </button>
              <div id="docs-upload-status" className="text-xs text-[var(--text-secondary)] ml-2">
                {uploadStatus}
              </div>
            </div>
          </div>
        )}

        {/* Input row */}
        <div id="llm-input-row" className="flex gap-2.5 mt-3">
          <input
            id="llm-prompt"
            type="text"
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder="Escribe tu pregunta al LLM (por ejemplo, explica un CVE o resume una noticia)..."
            className="flex-1 px-4 py-2.5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-app)] text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand-primary)]"
          />
          <button
            id="llm-send-btn"
            type="button"
            disabled={sending}
            onClick={() => handleSendMessage()}
            className="px-5 py-2.5 rounded-xl bg-[var(--brand-primary)] text-white text-xs font-semibold flex items-center gap-1.5 hover:bg-[var(--brand-primary-hover)] transition-all btn-bounce disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Enviar</span>
          </button>
        </div>
      </div>
    </div>
  );
};
