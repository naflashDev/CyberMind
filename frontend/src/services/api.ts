/**
 * @file api.ts
 * @author naflashDev
 * @brief Centralized HTTP client for the CyberMind FastAPI backend.
 * @details Connects to all backend endpoints preserving the exact contract of the original UI.
 */

const API_BASE = '/api';

export interface ConfigParam {
  key: string;
  value: string;
  type: 'boolean' | 'string' | string;
}

export interface ConfigFileBlock {
  file: string;
  params: ConfigParam[];
}

export interface ConversationSummary {
  id: number;
  title: string;
  created_at: string;
}

export interface ConversationMessage {
  id?: number;
  role: 'user' | 'assistant' | 'bot' | string;
  text: string;
  timestamp: string;
}

export interface ConversationDetail {
  id: number;
  title: string;
  created_at?: string;
  messages: ConversationMessage[];
}

export async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = endpoint.startsWith('http')
    ? endpoint
    : `${API_BASE}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

  const headers = new Headers(options?.headers || {});
  if (!headers.has('Content-Type') && !(options?.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    let msg = errorText || response.statusText;
    try {
      const parsed = JSON.parse(errorText);
      if (parsed && typeof parsed === 'object') {
        msg = parsed.detail || parsed.message || errorText;
      }
    } catch {
      // Leave raw text
    }
    throw new Error(msg);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.toLowerCase().includes('application/json')) {
    return response.json() as Promise<T>;
  }

  const text = await response.text();
  try {
    return JSON.parse(text) as T;
  } catch {
    return text as unknown as T;
  }
}

export const api = {
  // System Health, Status & Workers
  getHealth: () =>
    request<{ status: string; infra_ready: boolean; ui_initialized: boolean }>('/health'),
  getStatus: () =>
    request<{
      infra_ready?: boolean;
      infra_error?: string;
      ui_initialized?: boolean;
      workers?: Record<string, boolean>;
      [key: string]: unknown;
    }>('/status'),
  toggleWorker: (name: string, enabled: boolean) =>
    request<{ status?: string }>(`/workers/${encodeURIComponent(name)}`, {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    }),
  shutdownApp: () =>
    request<{ reload?: boolean }>('/workers/shutdown', {
      method: 'POST',
    }),

  // Config (.ini files)
  getConfig: () => request<{ files: ConfigFileBlock[] }>('/config'),
  saveConfigFile: (file: string, params: ConfigParam[]) =>
    request('/config', {
      method: 'POST',
      body: JSON.stringify({ file, params }),
    }),

  // Documentation
  getDocsList: () => request<string[]>('/docs/list'),
  getDocReadme: () =>
    fetch(`${API_BASE}/docs/readme`).then(async (r) => {
      if (!r.ok) throw new Error('No se pudo cargar README.md');
      return r.text();
    }),
  getDocFile: (filename: string) =>
    fetch(`${API_BASE}/docs/file/${encodeURIComponent(filename)}`).then(async (r) => {
      if (!r.ok) throw new Error(`No se pudo cargar ${filename}`);
      return r.text();
    }),

  // LLM Chat & Documents
  getConversations: () => request<ConversationSummary[]>('/llm/conversations'),
  createConversation: (title: string = 'Chat') =>
    request<ConversationSummary>('/llm/conversations', {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),
  getConversation: (id: number) => request<ConversationDetail>(`/llm/conversations/${id}`),
  deleteConversation: (id: number) =>
    request(`/llm/conversations/${id}`, {
      method: 'DELETE',
    }),
  queryLLM: (payload: { prompt: string; conversation_id?: number | null; top_k?: number }) =>
    request<{ response?: string; result?: string }>('/llm/query', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getDocFolders: () => request<{ folders: { name: string; path: string }[] }>('/documents/folders'),
  uploadDocuments: (formData: FormData) =>
    request<{ results?: Array<{ message?: string; file?: string; doc_id?: string }> }>(
      '/documents/upload',
      {
        method: 'POST',
        body: formData,
      }
    ),

  // Code Scanning PDF Generation & Helpers
  scanCodeText: (code: string) =>
    request<{
      vulnerabilities: unknown[];
      vulnerabilities_full: unknown[];
      llm_enabled: boolean;
      pdf_base64: string | null;
    }>('/code/scan-text', {
      method: 'POST',
      body: JSON.stringify({ code }),
    }),
  scanCodeFile: (formData: FormData) =>
    request<{
      vulnerabilities: unknown[];
      vulnerabilities_full: unknown[];
      llm_enabled: boolean;
      pdf_base64: string | null;
    }>('/code/scan-file', {
      method: 'POST',
      body: formData,
    }),
  generateCodePdf: (vulnerabilities: unknown[]) =>
    request<{ pdf_base64: string }>('/code/generate-pdf', {
      method: 'POST',
      body: JSON.stringify({ vulnerabilities }),
    }),
};
