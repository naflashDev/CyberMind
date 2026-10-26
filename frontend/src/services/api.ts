/**
 * @file api.ts
 * @author naflashDev
 * @brief Cliente HTTP centralizado para CyberMind API.
 * @details Conecta con los endpoints del backend FastAPI soportando baseURL configurable.
 */

const API_BASE = '/api';

export async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  
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
    throw new Error(`Error ${response.status}: ${errorText || response.statusText}`);
  }

  // Handle JSON response
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json() as Promise<T>;
  }

  return response.text() as unknown as Promise<T>;
}

export const api = {
  // System Health & Status
  getHealth: () => request<{ status: string; infra_ready: boolean; ui_initialized: boolean }>('/health'),
  getStatus: () => request<Record<string, unknown>>('/status'),

  // Config
  getConfigFiles: () => request<{ files: { name: string; content: string }[] }>('/config/files'),
  saveConfigFile: (name: string, content: string) =>
    request('/config/save', {
      method: 'POST',
      body: JSON.stringify({ name, content }),
    }),

  // Documentation
  getDocsList: () => request<{ files: string[] }>('/docs/list'),
  getDocContent: (filename: string) => request<{ content: string }>(`/docs/file/${filename}`),

  // LLM Chat & Documents
  getConversations: () => request<Array<{ id: number; title: string; created_at: string }>>('/llm/conversations'),
  getConversationMessages: (id: number) => request<Array<{ role: string; content: string; created_at: string }>>(`/llm/conversations/${id}/messages`),
  sendLLMMessage: (payload: { prompt?: string; conversation_id?: number; model?: string }) =>
    request<{ response: string; conversation_id: number }>('/llm/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getDocFolders: () => request<{ folders: { name: string; path: string }[] }>('/documents/folders'),
  uploadDocument: (formData: FormData) =>
    request('/documents/upload', {
      method: 'POST',
      body: formData,
    }),

  // Code Analysis
  scanCodeText: (code: string) =>
    request<{ vulnerabilities: unknown[]; vulnerabilities_full: unknown[]; llm_enabled: boolean; pdf_base64: string | null }>('/code/scan-text', {
      method: 'POST',
      body: JSON.stringify({ code }),
    }),
  scanCodeFile: (formData: FormData) =>
    request<{ vulnerabilities: unknown[]; vulnerabilities_full: unknown[]; llm_enabled: boolean; pdf_base64: string | null }>('/code/scan-file', {
      method: 'POST',
      body: formData,
    }),

  // Network Analysis
  scanNetworkPort: (payload: { host: string; ports?: number[]; timeout?: number; use_nmap?: boolean }) =>
    request<{ results: unknown[] }>('/network/scan', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  scanNetworkRange: (payload: { cidr?: string; start?: string; end?: string; ports?: number[]; timeout?: number; use_nmap?: boolean }) =>
    request<{ results: unknown[] }>('/network/scan-range', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
