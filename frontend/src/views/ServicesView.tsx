/**
 * @file ServicesView.tsx
 * @author naflashDev
 * @brief Complete replication of the FastAPI Services panel from index.html and ui.js with modern Lucide icons.
 * @details Includes OSINT (Scrapy, SpaCy, Tiny, LLM), Code Scanning, Hashed, Network, and Status controllers,
 *          preserving per-operation form & result caches and specialized visual cards.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Zap,
  Globe,
  Code2,
  KeyRound,
  Network,
  Activity,
  ChevronDown,
  ChevronRight,
  Search,
  Save,
  Play,
  List,
  RefreshCw,
  Rss,
  Brain,
  Bot,
  Settings,
  Trash2,
  Copy,
  FileDown,
  Upload,
  Info,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Lock,
} from 'lucide-react';
import { api } from '../services/api';

export interface OperationParam {
  name: string;
  type: 'text' | 'textarea' | 'file' | 'enum' | 'number' | 'checkbox';
  placeholder?: string;
  label?: string;
  large?: boolean;
  accept?: string;
  dragdrop?: boolean;
  options?: string[];
  default?: string | number | boolean;
}

export interface OperationDef {
  id: string;
  title: string;
  method: 'GET' | 'POST';
  path: string;
  params: OperationParam[];
  desc: string;
}

const CONTROLLERS: Record<string, OperationDef[]> = {
  'Code Scanning': [
    {
      id: 'scan-code-text',
      title: 'Analizar código (texto)',
      method: 'POST',
      path: '/code/scan-text',
      params: [
        {
          name: 'code',
          type: 'textarea',
          placeholder: 'Pega aquí el código fuente a analizar',
          large: true,
        },
      ],
      desc: 'Analiza un fragmento de código recibido como texto y muestra vulnerabilidades encontradas e informe PDF.',
    },
    {
      id: 'scan-code-file',
      title: 'Analizar código (archivo)',
      method: 'POST',
      path: '/code/scan-file',
      params: [
        {
          name: 'file',
          type: 'file',
          label: 'Archivo de código (drag & drop)',
          accept: '.py,.js,.java,.c,.cpp,.rb,.go',
          dragdrop: true,
        },
      ],
      desc: 'Sube un archivo de código fuente y muestra vulnerabilidades encontradas e informe PDF.',
    },
  ],
  Hashed: [
    {
      id: 'hash-phrase',
      title: 'Hashear frase',
      method: 'POST',
      path: '/hashed/hash',
      params: [
        { name: 'phrase', type: 'text', placeholder: 'Texto a hashear' },
        {
          name: 'algorithm',
          type: 'enum',
          options: ['MD5', 'SHA256', 'SHA512'],
          default: 'SHA256',
          label: 'Algoritmo',
        },
      ],
      desc: 'Genera el hash de una frase usando el algoritmo seleccionado (MD5, SHA256, SHA512).',
    },
    {
      id: 'unhash',
      title: 'Deshashear (auto, múltiple)',
      method: 'POST',
      path: '/hashed/unhash',
      params: [
        {
          name: 'hashes',
          type: 'textarea',
          placeholder: 'Introduce uno o más hashes, uno por línea',
        },
        {
          name: 'max_len',
          type: 'number',
          placeholder: 'Longitud máxima fuerza bruta (default 20)',
          default: 20,
          label: 'Long. máxima',
        },
      ],
      desc: 'Introduce uno o más hashes (uno por línea). Detecta tipo, busca en BBDD y fuerza bruta si no existe.',
    },
    {
      id: 'unhash-file',
      title: 'Deshashear archivo (drag & drop)',
      method: 'POST',
      path: '/hashed/unhash-file',
      params: [
        {
          name: 'file',
          type: 'file',
          label: 'Archivo de hashes (txt)',
          accept: '.txt',
          dragdrop: true,
        },
      ],
      desc: 'Sube un archivo de texto con hashes (uno por línea). Cada hash se procesa con timeout de 1 minuto. El resultado se muestra en formato tabla.',
    },
    {
      id: 'upload-hash-file',
      title: 'Subir palabras+hash (drag & drop)',
      method: 'POST',
      path: '/hashed/upload-hash-file',
      params: [
        {
          name: 'file',
          type: 'file',
          label: 'Archivo palabra+hash (txt)',
          accept: '.txt',
          dragdrop: true,
        },
      ],
      desc: 'Sube un archivo de texto donde cada línea contiene una palabra y su hash, separados por coma, espacio o tabulación. El sistema detecta el tipo de hash y almacena cada entrada en la base de datos. Ideal para cargas masivas mediante drag & drop.',
    },
    {
      id: 'hash-file',
      title: 'Hash de archivo (drag & drop)',
      method: 'POST',
      path: '/hashed/hash-file',
      params: [
        {
          name: 'file',
          type: 'file',
          label: 'Archivo de palabras (txt)',
          accept: '.txt',
          dragdrop: true,
        },
        {
          name: 'algorithm',
          type: 'enum',
          options: ['MD5', 'SHA256', 'SHA512'],
          default: 'SHA256',
          label: 'Algoritmo',
        },
      ],
      desc: 'Sube un archivo de texto donde cada línea es una palabra. Selecciona el algoritmo y obtén el hash de cada palabra en tarjetas visuales.',
    },
  ],
  Scrapy: [
    {
      id: 'scrape-news',
      title: 'Scrape News',
      method: 'GET',
      path: '/newsSpider/scrape-news',
      params: [],
      desc: 'Extrae noticias desde las fuentes configuradas y las normaliza.',
    },
    {
      id: 'start-google-alerts',
      title: 'Start Google Alerts',
      method: 'GET',
      path: '/newsSpider/start-google-alerts',
      params: [],
      desc: 'Inicia la recolección de alertas de Google configuradas.',
    },
    {
      id: 'save-feed-google-alerts',
      title: 'Save Feed Google Alerts',
      method: 'POST',
      path: '/newsSpider/save-feed-google-alerts',
      params: [{ name: 'link', type: 'text', placeholder: 'URL o texto del feed' }],
      desc: 'Guarda un feed (o URL) de Google Alerts en la base de datos.',
    },
    {
      id: 'scrapy-google-dk-feeds',
      title: 'Scrapy Google DK Feeds',
      method: 'GET',
      path: '/newsSpider/scrapy/google-dk/feeds',
      params: [],
      desc: 'Rastrea y lista feeds encontrados para Google DK (feeds).',
    },
    {
      id: 'scrapy-google-dk-news',
      title: 'Scrapy Google DK News',
      method: 'GET',
      path: '/newsSpider/scrapy/google-dk/news',
      params: [],
      desc: 'Rastrea artículos/noticias desde Google DK.',
    },
  ],
  SpaCy: [
    {
      id: 'start-spacy',
      title: 'Start SpaCy',
      method: 'GET',
      path: '/start-spacy',
      params: [],
      desc: 'Inicia o carga el pipeline de SpaCy para procesamiento de texto.',
    },
  ],
  Tiny: [
    {
      id: 'search-and-insert-rss',
      title: 'Search and Insert RSS',
      method: 'GET',
      path: '/postgre-ttrss/search-and-insert-rss',
      params: [{ name: 'link', type: 'text', placeholder: 'consulta (opcional)' }],
      desc: 'Busca elementos RSS por consulta e inserta los nuevos en TinyRSS/Postgres.',
    },
    {
      id: 'feeds',
      title: 'List Feeds',
      method: 'GET',
      path: '/postgre-ttrss/feeds',
      params: [],
      desc: 'Lista los feeds almacenados en la base de datos.',
    },
  ],
  LLM: [
    {
      id: 'llm-updater',
      title: 'LLM Updater',
      method: 'GET',
      path: '/llm/updater',
      params: [],
      desc: 'Inicia el updater en background (llm_updater).',
    },
  ],
  Network: [
    {
      id: 'network-scan',
      title: 'Analisis de redes (scan)',
      method: 'POST',
      path: '/network/scan',
      params: [
        { name: 'host', type: 'text', placeholder: 'IP o hostname' },
        { name: 'ports', type: 'text', placeholder: 'puertos separados por comas (opcional)' },
        { name: 'use_nmap', type: 'checkbox', label: 'Usar nmap (recomendado)', default: true },
      ],
      desc: 'Escanea puertos comunes y devuelve servicios heurísticos. Asegúrate de tener permiso para escanear el host.',
    },
    {
      id: 'network-scan-range',
      title: 'Analisis de redes (rango)',
      method: 'POST',
      path: '/network/scan_range',
      params: [
        { name: 'cidr', type: 'text', placeholder: 'CIDR (ej. 192.168.1.0/28)' },
        { name: 'start', type: 'text', placeholder: 'IP inicio (ej. 192.168.1.1)' },
        { name: 'end', type: 'text', placeholder: 'IP fin (opcional)' },
        { name: 'ports', type: 'text', placeholder: 'puertos separados por comas (opcional)' },
        {
          name: 'concurrency',
          type: 'text',
          placeholder: 'concurrency (opcional, default 20)',
        },
        {
          name: 'use_nmap',
          type: 'checkbox',
          label: 'Usar nmap si está disponible',
          default: true,
        },
      ],
      desc: 'Escanea un rango de IPs y devuelve puertos abiertos/cerrados por IP. Usa con permiso.',
    },
    {
      id: 'network-ports',
      title: 'List Common Ports',
      method: 'GET',
      path: '/network/ports',
      params: [],
      desc: 'Lista puertos comunes sugeridos para escaneo.',
    },
  ],
  Status: [
    {
      id: 'system-status-op',
      title: 'System Status',
      method: 'GET',
      path: '/status',
      params: [],
      desc: 'Muestra el estado de la infraestructura, UI y workers en ejecución.',
    },
  ],
};

const OSINT_CONTROLLERS = ['Scrapy', 'SpaCy', 'Tiny', 'LLM'];
const MAIN_CONTROLLERS = ['Code Scanning', 'Hashed', 'Network', 'Status'];

const WORKER_FRIENDLY: Record<string, { name: string; info: string }> = {
  google_alerts: {
    name: 'Google Alerts',
    info: 'Recolecta alertas de Google configuradas y las procesa periódicamente.',
  },
  rss_extractor: {
    name: 'Extractor RSS',
    info: 'Extrae y normaliza feeds RSS de ciberseguridad desde fuentes configuradas.',
  },
  scraping_feeds: {
    name: 'Scraping Feeds',
    info: 'Rastrea y actualiza feeds de noticias de ciberseguridad.',
  },
  scraping_news: {
    name: 'Scraping News',
    info: 'Extrae artículos y noticias de fuentes externas para su análisis.',
  },
  spacy_nlp: {
    name: 'NLP (spaCy)',
    info: 'Procesa y etiqueta entidades en textos usando spaCy cada 24h.',
  },
  llm_updater: {
    name: 'LLM Updater',
    info: 'Actualiza el modelo LLM y el dataset de CVEs cada 7 días.',
  },
  dynamic_spider: {
    name: 'Spider Dinámico',
    info: 'Ejecuta spiders Scrapy configurados dinámicamente desde la base de datos.',
  },
  vector_ingest: {
    name: 'Ingesta de Vectores',
    info: 'Escanea ./data/documents y normaliza/sube documentos al vectorstore (Chroma) para búsqueda semántica. Evita reindexar documentos ya indexados.',
  },
  vector_retention: {
    name: 'Retención de Vectores',
    info: 'Elimina vectores y conversaciones antiguas según TTL (por defecto 7 días). Mantiene el tamaño y frescura del índice.',
  },
};

interface CachedOpState {
  values: Record<string, string | number | boolean>;
  file: File | null;
  loading: boolean;
  error: string | null;
  status: number | null;
  result: unknown;
  submittedPhrase?: string;
  submittedAlgorithm?: string;
}

/**
 * @brief Return a modern Lucide icon component for a controller group.
 */
function getControllerIcon(name: string) {
  switch (name) {
    case 'OSINT':
      return Globe;
    case 'Code Scanning':
      return Code2;
    case 'Hashed':
      return KeyRound;
    case 'Network':
      return Network;
    case 'Status':
      return Activity;
    case 'Scrapy':
      return Search;
    case 'SpaCy':
      return Brain;
    case 'Tiny':
      return Rss;
    case 'LLM':
      return Bot;
    default:
      return Zap;
  }
}

/**
 * @brief Return a modern Lucide icon component for an individual operation.
 */
function getOperationIcon(title: string) {
  const t = title.toLowerCase();
  if (t.includes('scan') || t.includes('analizar') || t.includes('analisis')) return Search;
  if (t.includes('save') || t.includes('subir')) return Save;
  if (t.includes('start') || t.includes('scrape')) return Play;
  if (t.includes('list')) return List;
  if (t.includes('updater')) return RefreshCw;
  if (t.includes('status')) return Activity;
  if (t.includes('feeds') || t.includes('rss')) return Rss;
  if (t.includes('spacy')) return Brain;
  if (t.includes('llm')) return Bot;
  if (t.includes('hash') || t.includes('deshashear')) return KeyRound;
  return Settings;
}

/**
 * @brief Compute numerical severity rank for sorting vulnerabilities.
 */
function getSeverityRank(s: unknown): number {
  if (!s && s !== 0) return 0;
  const v = String(s).toLowerCase();
  if (/critical|crit|cve-critical/.test(v)) return 5;
  if (/high|h/.test(v)) return 4;
  if (/medium|med|m/.test(v)) return 3;
  if (/low|l/.test(v)) return 2;
  if (/info|informational|notice/.test(v)) return 1;
  const n = Number(String(s).replace(/[^0-9.]/g, ''));
  if (!Number.isNaN(n)) return Math.min(5, Math.max(0, Math.round(n)));
  return 0;
}

export const ServicesView: React.FC = () => {
  // Collapse state: all collapsed by default as in ui.js
  const [osintCollapsed, setOsintCollapsed] = useState(true);
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    Object.keys(CONTROLLERS).forEach((k) => {
      init[k] = true;
    });
    return init;
  });

  const [selectedController, setSelectedController] = useState<string | null>(null);
  const [selectedOp, setSelectedOp] = useState<OperationDef | null>(null);

  // Per-operation cache for inputs, files, and results
  const [opsCache, setOpsCache] = useState<Record<string, CachedOpState>>({});

  // Toast state
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Status panel state for /status operation
  const [statusData, setStatusData] = useState<{
    infra_ready?: boolean;
    infra_error?: string;
    ui_initialized?: boolean;
    workers?: Record<string, boolean>;
  } | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [togglingWorker, setTogglingWorker] = useState<string | null>(null);

  // Host collapse state in range scan
  const [collapsedHosts, setCollapsedHosts] = useState<Record<string, boolean>>({});

  // Friendly / Raw JSON panel collapse state
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [generatingPdf, setGeneratingPdf] = useState(false);

  const showToast = useCallback((msg: string, ms = 2000) => {
    setToastMsg(msg);
    setTimeout(() => {
      setToastMsg((prev) => (prev === msg ? null : prev));
    }, ms);
  }, []);

  /**
   * @brief Initialize default state for an operation if not cached yet.
   */
  const getOpState = (op: OperationDef): CachedOpState => {
    if (opsCache[op.id]) return opsCache[op.id];
    const defaults: Record<string, string | number | boolean> = {};
    op.params.forEach((p) => {
      if (p.default !== undefined) {
        defaults[p.name] = p.default;
      } else if (p.type === 'checkbox') {
        defaults[p.name] = true;
      } else {
        defaults[p.name] = '';
      }
    });
    return {
      values: defaults,
      file: null,
      loading: false,
      error: null,
      status: null,
      result: null,
    };
  };

  const updateOpState = (opId: string, updater: (prev: CachedOpState) => CachedOpState) => {
    setOpsCache((prev) => {
      const opDef = Object.values(CONTROLLERS)
        .flat()
        .find((o) => o.id === opId);
      const current =
        prev[opId] ||
        (opDef
          ? getOpState(opDef)
          : {
              values: {},
              file: null,
              loading: false,
              error: null,
              status: null,
              result: null,
            });
      return {
        ...prev,
        [opId]: updater(current),
      };
    });
  };

  /**
   * @brief Fetch system status when Status operation is active.
   */
  const fetchSystemStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const data = await api.getStatus();
      setStatusData(data);
    } catch (e) {
      console.error('Error fetching status:', e);
    } finally {
      setStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedOp?.path === '/status') {
      fetchSystemStatus();
      const interval = setInterval(fetchSystemStatus, 10000);
      return () => clearInterval(interval);
    }
  }, [selectedOp, fetchSystemStatus]);

  const handleToggleWorker = async (name: string, currentEnabled: boolean) => {
    setTogglingWorker(name);
    try {
      await api.toggleWorker(name, !currentEnabled);
      showToast(`${!currentEnabled ? 'Activated' : 'Stopped'} ${name}`);
      setTimeout(fetchSystemStatus, 300);
    } catch (err) {
      showToast(`Error toggling worker: ${(err as Error).message}`);
    } finally {
      setTogglingWorker(null);
    }
  };

  const handleToggleAllWorkers = async (enable: boolean) => {
    if (!statusData?.workers) return;
    setStatusLoading(true);
    try {
      const names = Object.keys(statusData.workers);
      const results = await Promise.allSettled(
        names.map((name) => api.toggleWorker(name, enable))
      );
      const succeeded = results.filter((r) => r.status === 'fulfilled').length;
      showToast(`${enable ? 'Started' : 'Stopped'} ${succeeded} workers`);
      setTimeout(fetchSystemStatus, 400);
    } catch (err) {
      showToast(`Error toggling workers: ${(err as Error).message}`);
    } finally {
      setStatusLoading(false);
    }
  };

  const toggleSection = (name: string) => {
    setCollapsedSections((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const handleSelectOp = (controllerName: string, op: OperationDef) => {
    setSelectedController(controllerName);
    setSelectedOp(op);
    if (!opsCache[op.id]) {
      setOpsCache((prev) => ({ ...prev, [op.id]: getOpState(op) }));
    }
  };

  /**
   * @brief Clear current operation form inputs and result container.
   */
  const handleClearFormAndResult = (op: OperationDef) => {
    const defaults: Record<string, string | number | boolean> = {};
    op.params.forEach((p) => {
      if (p.default !== undefined) {
        defaults[p.name] = p.default;
      } else if (p.type === 'checkbox') {
        defaults[p.name] = false;
      } else {
        defaults[p.name] = '';
      }
    });
    updateOpState(op.id, () => ({
      values: defaults,
      file: null,
      loading: false,
      error: null,
      status: null,
      result: null,
    }));
  };

  /**
   * @brief Execute the selected operation against the FastAPI backend.
   */
  const handleSubmitOp = async (e: React.FormEvent, op: OperationDef) => {
    e.preventDefault();
    const state = getOpState(op);

    // Validate required file input
    if (op.params.some((p) => p.type === 'file') && !state.file) {
      updateOpState(op.id, (prev) => ({
        ...prev,
        error: 'Debes seleccionar un archivo antes de enviar.',
      }));
      return;
    }

    const phraseVal = String(state.values.phrase || '');
    const algVal = String(state.values.algorithm || 'SHA256');

    updateOpState(op.id, (prev) => ({
      ...prev,
      loading: true,
      error: null,
      submittedPhrase: phraseVal,
      submittedAlgorithm: algVal,
    }));

    try {
      const baseUrl = `/api${op.path}`;
      let resp: Response;

      if (op.method === 'GET') {
        const params = new URLSearchParams();
        Object.entries(state.values).forEach(([k, v]) => {
          if (v !== undefined && v !== null && String(v).trim() !== '') {
            params.append(k, String(v));
          }
        });
        const finalUrl = params.toString() ? `${baseUrl}?${params.toString()}` : baseUrl;
        resp = await fetch(finalUrl);
      } else if (
        op.path === '/hashed/unhash-file' ||
        op.path === '/hashed/upload-hash-file' ||
        op.path === '/hashed/hash-file' ||
        op.path === '/code/scan-file'
      ) {
        const fd = new FormData();
        if (state.file) {
          fd.append('file', state.file);
        }
        if (op.path === '/hashed/hash-file' && state.values.algorithm) {
          fd.append('algorithm', String(state.values.algorithm));
        }
        resp = await fetch(baseUrl, { method: op.method, body: fd });
      } else {
        const payload: Record<string, unknown> = {};
        Object.entries(state.values).forEach(([k, v]) => {
          if (typeof v === 'string' && v.trim() === '') return;
          if (k === 'ports' && typeof v === 'string') {
            const parsed = v
              .split(',')
              .map((s) => parseInt(s.trim(), 10))
              .filter((n) => !Number.isNaN(n));
            if (parsed.length > 0) payload.ports = parsed;
            return;
          }
          if (k === 'max_len' || k === 'concurrency') {
            const num = Number(v);
            if (!Number.isNaN(num)) payload[k] = num;
            return;
          }
          payload[k] = v;
        });

        resp = await fetch(baseUrl, {
          method: op.method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      }

      const contentType = resp.headers.get('content-type') || '';
      let parsedJson: unknown = null;
      let rawText: string | null = null;

      if (contentType.toLowerCase().includes('application/json')) {
        try {
          parsedJson = await resp.json();
        } catch {
          rawText = await resp.text();
        }
      } else {
        rawText = await resp.text();
        try {
          parsedJson = JSON.parse(rawText);
        } catch {
          parsedJson = null;
        }
      }

      if (!resp.ok) {
        let errMsg = 'Error desconocido.';
        if (parsedJson && typeof parsedJson === 'object') {
          const obj = parsedJson as Record<string, unknown>;
          errMsg = String(obj.detail || obj.message || JSON.stringify(obj));
        } else if (rawText) {
          errMsg = rawText;
        }
        updateOpState(op.id, (prev) => ({
          ...prev,
          loading: false,
          status: resp.status,
          error: errMsg,
        }));
        return;
      }

      const workerStartPaths = new Set([
        '/newsSpider/scrape-news',
        '/newsSpider/start-google-alerts',
        '/newsSpider/scrapy/google-dk/news',
        '/newsSpider/scrapy/google-dk/feeds',
        '/start-spacy',
        '/postgre-ttrss/search-and-insert-rss',
        '/llm/updater',
      ]);
      if (workerStartPaths.has(op.path)) {
        showToast(`${op.title} iniciada`);
      }

      updateOpState(op.id, (prev) => ({
        ...prev,
        loading: false,
        status: resp.status,
        error: null,
        result: parsedJson !== null ? parsedJson : rawText,
      }));
    } catch (err) {
      updateOpState(op.id, (prev) => ({
        ...prev,
        loading: false,
        error: (err as Error).message,
      }));
    }
  };

  /**
   * @brief Render friendly recursive key-value view for generic JSON responses.
   */
  const renderFriendlyValue = (value: unknown, depth = 0): React.ReactNode => {
    if (value === null || value === undefined) {
      return <span className="text-[var(--text-muted)] italic">(nulo)</span>;
    }
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      return <span className="text-[var(--text-primary)]">{String(value)}</span>;
    }
    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <span className="text-[var(--text-muted)] italic">(vacío)</span>;
      }
      const items = value.slice(0, 200);
      return (
        <ul className="list-disc pl-5 space-y-1 my-1">
          {items.map((it, idx) => (
            <li key={idx}>{renderFriendlyValue(it, depth + 1)}</li>
          ))}
          {value.length > 200 && (
            <li className="text-[var(--text-muted)]">... {value.length - 200} más</li>
          )}
        </ul>
      );
    }
    if (typeof value === 'object') {
      const obj = value as Record<string, unknown>;
      if (depth >= 2) {
        return (
          <details className="my-1">
            <summary className="cursor-pointer text-[var(--brand-primary)] text-xs font-semibold">
              Objeto (mostrar JSON)
            </summary>
            <pre className="mt-1 p-2 rounded bg-[var(--bg-app)] text-xs font-mono overflow-auto">
              {JSON.stringify(obj, null, 2)}
            </pre>
          </details>
        );
      }
      return (
        <div className="space-y-1">
          {Object.entries(obj).map(([k, v]) => (
            <div key={k} className="text-xs">
              <span className="font-semibold text-[var(--brand-primary)] mr-1.5">{k}:</span>
              {renderFriendlyValue(v, depth + 1)}
            </div>
          ))}
        </div>
      );
    }
    return <span>{String(value)}</span>;
  };

  /**
   * @brief Render specialized result view depending on the operation path/id.
   */
  const renderOperationResult = (op: OperationDef, state: CachedOpState) => {
    if (state.loading) {
      return (
        <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] p-4">
          <RefreshCw className="w-4 h-4 animate-spin text-[var(--brand-primary)]" />
          <span>Cargando...</span>
        </div>
      );
    }

    if (state.error) {
      return (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm font-semibold">
          {state.error}
        </div>
      );
    }

    if (state.result === null || state.result === undefined) {
      return (
        <div className="text-xs text-[var(--text-muted)] p-2">Respuesta aquí...</div>
      );
    }

    const resObj = state.result as Record<string, any>;

    // 1. /hashed/hash
    if (op.path === '/hashed/hash' && resObj && resObj.hashed_value) {
      return (
        <div className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-2xl p-6 max-w-3xl mx-auto shadow-lg flex items-center gap-5">
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center shrink-0">
            <KeyRound className="w-6 h-6 text-amber-400" />
          </div>
          <div className="space-y-1.5 min-w-0 flex-1">
            <div className="text-sm text-[var(--text-primary)]">
              <strong className="text-[var(--text-secondary)]">Palabra:</strong>{' '}
              <span className="text-amber-400 font-semibold">{state.submittedPhrase}</span>
            </div>
            <div className="text-sm text-[var(--text-primary)] break-all">
              <strong className="text-[var(--text-secondary)]">Hash:</strong>{' '}
              <span className="font-mono text-sky-400">{resObj.hashed_value}</span>
            </div>
            <div className="text-sm text-[var(--text-primary)]">
              <strong className="text-[var(--text-secondary)]">Algoritmo:</strong>{' '}
              <span className="text-amber-300 font-semibold">{state.submittedAlgorithm}</span>
            </div>
          </div>
        </div>
      );
    }

    // 2. /code/scan-text & /code/scan-file
    if (op.path === '/code/scan-text' || op.path === '/code/scan-file') {
      let vulns: any[] = [];
      let vulnsFull: any[] = [];
      let pdfB64: string | null = null;

      if (Array.isArray(resObj)) {
        vulns = resObj.slice();
        vulnsFull = resObj.slice();
      } else if (resObj && typeof resObj === 'object') {
        if (Array.isArray(resObj.vulnerabilities)) {
          vulns = resObj.vulnerabilities.slice();
          vulnsFull = Array.isArray(resObj.vulnerabilities_full)
            ? resObj.vulnerabilities_full
            : vulns;
        } else if (Array.isArray(resObj.vulnerabilities_full)) {
          vulns = resObj.vulnerabilities_full.slice();
          vulnsFull = vulns;
        }
        pdfB64 = resObj.pdf_base64 || null;
      }

      vulns.sort((a, b) => {
        const ra = getSeverityRank(a?.severity);
        const rb = getSeverityRank(b?.severity);
        if (rb !== ra) return rb - ra;
        const fa = a?.filename ? String(a.filename) : '';
        const fb = b?.filename ? String(b.filename) : '';
        const cmp = fa.localeCompare(fb);
        if (cmp !== 0) return cmp;
        return (Number(a?.line) || 0) - (Number(b?.line) || 0);
      });

      if (vulns.length === 0) {
        return (
          <div className="text-emerald-400 font-semibold text-sm p-4">
            No se encontraron vulnerabilidades.
          </div>
        );
      }

      const handleDownloadOrGeneratePdf = async () => {
        if (pdfB64) {
          const blob = new Blob([Uint8Array.from(atob(pdfB64), (c) => c.charCodeAt(0))], {
            type: 'application/pdf',
          });
          const link = document.createElement('a');
          link.href = URL.createObjectURL(blob);
          link.download = 'informe_code_scan.pdf';
          document.body.appendChild(link);
          link.click();
          setTimeout(() => document.body.removeChild(link), 100);
          return;
        }

        setGeneratingPdf(true);
        try {
          const data = await api.generateCodePdf(vulnsFull.length ? vulnsFull : vulns);
          if (!data.pdf_base64) throw new Error('No se recibió PDF');
          const blob = new Blob(
            [Uint8Array.from(atob(data.pdf_base64), (c) => c.charCodeAt(0))],
            { type: 'application/pdf' }
          );
          const link = document.createElement('a');
          link.href = URL.createObjectURL(blob);
          link.download = 'informe_code_scan.pdf';
          document.body.appendChild(link);
          link.click();
          setTimeout(() => document.body.removeChild(link), 100);
          updateOpState(op.id, (prev) => ({
            ...prev,
            result: { ...(prev.result as object), pdf_base64: data.pdf_base64 },
          }));
        } catch (err) {
          showToast(`Error generando PDF: ${(err as Error).message}`);
        } finally {
          setGeneratingPdf(false);
        }
      };

      return (
        <div className="space-y-4">
          <button
            type="button"
            onClick={handleDownloadOrGeneratePdf}
            disabled={generatingPdf}
            className="btn-download-pdf px-4 py-2 rounded-xl bg-[var(--brand-primary)] text-white font-bold text-xs flex items-center gap-2 hover:bg-[var(--brand-primary-hover)] transition-all btn-bounce shadow-md disabled:opacity-50"
          >
            <FileDown className="w-4 h-4" />
            <span>
              {generatingPdf
                ? 'Generando informe...'
                : pdfB64
                ? 'Descargar informe PDF'
                : 'Generar y descargar informe PDF'}
            </span>
          </button>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {vulns.map((v, idx) => {
              const sev = String(v.severity || '').toLowerCase();
              const isHigh = sev === 'high' || sev === 'critical';
              const isMed = sev === 'medium';
              const borderColor = isHigh
                ? 'border-l-rose-500'
                : isMed
                ? 'border-l-amber-500'
                : 'border-l-emerald-500';
              const badgeClass = isHigh
                ? 'bg-rose-500 text-slate-950'
                : isMed
                ? 'bg-amber-500 text-slate-950'
                : 'bg-emerald-500 text-slate-950';

              const description = v.description || v.title || '-';
              const line = v.line !== undefined ? String(v.line) : '-';
              const filename = v.filename ? String(v.filename) : null;
              const cwe = v.cwe || '-';

              let cveList: string[] = [];
              if (v.cve && typeof v.cve === 'string') cveList.push(v.cve);
              if (v.cve_id && typeof v.cve_id === 'string') cveList.push(v.cve_id);
              if (Array.isArray(v.cves)) cveList = cveList.concat(v.cves.map(String));
              if (Array.isArray(v.references)) {
                cveList = cveList.concat(
                  v.references.map(String).filter((r: string) => /CVE-\d{4}-\d{4,}/i.test(r))
                );
              }
              cveList = Array.from(new Set(cveList.map((s) => s.toUpperCase())));

              return (
                <div
                  key={idx}
                  className={`vuln-card bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] border-l-4 ${borderColor} rounded-xl p-4 shadow-md flex flex-col justify-between`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      <div className="w-10 h-10 rounded-lg bg-[var(--bg-app)] flex items-center justify-center shrink-0">
                        {isHigh ? (
                          <ShieldAlert className="w-5 h-5 text-rose-500" />
                        ) : isMed ? (
                          <AlertTriangle className="w-5 h-5 text-amber-500" />
                        ) : (
                          <Info className="w-5 h-5 text-emerald-500" />
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div
                          className="font-bold text-sm text-[var(--text-primary)] truncate"
                          title={description}
                        >
                          {description}
                        </div>
                        <div className="text-xs text-[var(--text-secondary)] mt-1.5 flex flex-wrap gap-3">
                          <div>
                            <strong>Archivo:</strong>{' '}
                            {filename ? (
                              <span className="text-sky-400">{filename}</span>
                            ) : (
                              <span>-</span>
                            )}
                          </div>
                          <div>
                            <strong>Línea:</strong> {line}
                          </div>
                          <div>
                            <strong>CWE:</strong> {cwe}
                          </div>
                          <div>
                            <strong>Confidencialidad:</strong> {v.confidentiality || '-'}
                          </div>
                        </div>
                        {cveList.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {cveList.map((c) => (
                              <a
                                key={c}
                                href={`https://cve.org/search/?q=${encodeURIComponent(c)}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-2 py-0.5 rounded-md bg-sky-500/10 text-sky-300 border border-sky-500/20 font-bold text-[11px] hover:bg-sky-500/20"
                              >
                                {c}
                              </a>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-2 shrink-0">
                      <span className={`px-2.5 py-1 rounded-md font-bold text-[11px] ${badgeClass}`}>
                        {sev.toUpperCase() || 'INFO'}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          navigator.clipboard?.writeText(`Línea: ${line}\n${description}`);
                          showToast('Detalles copiados');
                        }}
                        className="copy-vuln-details px-2.5 py-1 rounded-md border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] flex items-center gap-1"
                      >
                        <Copy className="w-3 h-3" />
                        <span>Copiar</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    // 3. /network/scan
    if (op.path === '/network/scan') {
      let portResults: any[] = [];
      if (resObj && Array.isArray(resObj.results)) {
        portResults = resObj.results.slice();
      } else if (Array.isArray(resObj)) {
        portResults = resObj.slice();
      } else if (resObj && typeof resObj === 'object') {
        const keys = Object.keys(resObj);
        if (keys.length > 0 && keys.every((k) => !Number.isNaN(Number(k)))) {
          portResults = keys.map((k) => ({ port: k, ...resObj[k] }));
        }
      }

      if (portResults.length === 0) {
        return (
          <div className="text-xs text-[var(--text-muted)]">
            No se encontraron puertos o la respuesta está vacía.
          </div>
        );
      }

      portResults.sort((a, b) => {
        if (!!b.open !== !!a.open) return b.open ? 1 : -1;
        const aState = String(a?.state || '').toLowerCase().trim();
        const bState = String(b?.state || '').toLowerCase().trim();
        if (aState === 'filtered' && bState !== 'filtered') return 1;
        if (bState === 'filtered' && aState !== 'filtered') return -1;
        return (Number(a.port) || 0) - (Number(b.port) || 0);
      });

      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {portResults.map((r, idx) => {
            const rstate = String(r?.state || '').toLowerCase().trim();
            const product = r.product
              ? `${r.product}${r.version ? ` v${r.version}` : ''}`
              : '';
            return (
              <div
                key={idx}
                className="port-card bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-4 flex justify-between items-start gap-2"
              >
                <div className="space-y-1 min-w-0">
                  <div className="font-bold text-xl text-[var(--text-primary)]">{r.port}</div>
                  <div className="text-sm text-[var(--text-secondary)]">{r.service || ''}</div>
                  {product && <div className="text-xs text-[var(--text-muted)]">{product}</div>}
                  {Array.isArray(r.methods) && r.methods.length > 0 && (
                    <div className="text-xs text-[var(--text-secondary)] mt-1">
                      <strong>Métodos:</strong> {r.methods.join(', ')}
                    </div>
                  )}
                </div>
                <div className="flex flex-col items-end gap-1.5 shrink-0">
                  <span className="text-xs text-[var(--text-muted)]">Puerto</span>
                  {rstate === 'filtered' ? (
                    <span className="px-2 py-0.5 rounded bg-amber-500 text-white font-semibold text-xs">
                      FILTERED
                    </span>
                  ) : r.open ? (
                    <span className="px-2 py-0.5 rounded bg-emerald-600 text-white font-semibold text-xs">
                      OPEN
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded bg-rose-600 text-white font-semibold text-xs">
                      CLOSED
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      );
    }

    // 4. /network/ports
    if (op.path === '/network/ports') {
      const items: any[] = Array.isArray(resObj?.common_ports) ? resObj.common_ports : [];
      if (items.length === 0) {
        return <div className="text-xs text-[var(--text-muted)]">No hay puertos comunes listados.</div>;
      }
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {items.map((it, idx) => (
            <div
              key={idx}
              className="port-card bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-3.5 flex justify-between items-center"
            >
              <div>
                <div className="font-bold text-base text-[var(--text-primary)]">{it.port}</div>
                <div className="text-xs text-[var(--text-secondary)] mt-0.5">{it.service || ''}</div>
              </div>
              <div className="flex flex-col items-end gap-1">
                <span className="text-[11px] text-[var(--text-muted)]">Puerto</span>
                {it.state === 'filtered' ? (
                  <span className="px-2 py-0.5 rounded bg-amber-500 text-white font-semibold text-xs">
                    FILTERED
                  </span>
                ) : it.open ? (
                  <span className="px-2 py-0.5 rounded bg-emerald-600 text-white font-semibold text-xs">
                    OPEN
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded bg-rose-600 text-white font-semibold text-xs">
                    CLOSED
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      );
    }

    // 5. /network/scan_range
    if (op.path === '/network/scan_range') {
      const rawHosts: any[] = Array.isArray(resObj?.hosts) ? resObj.hosts : [];
      if (rawHosts.length === 0) {
        return <div className="text-xs text-[var(--text-muted)]">No se obtuvieron resultados.</div>;
      }

      const hosts = rawHosts
        .map((h) => {
          const results = Array.isArray(h.results) ? h.results.slice() : [];
          results.sort((a: any, b: any) => {
            const aOpen = !!a.open;
            const bOpen = !!b.open;
            if (aOpen !== bOpen) return aOpen ? -1 : 1;
            return (Number(a.port) || 0) - (Number(b.port) || 0);
          });
          const openCount = results.filter((r: any) => !!r.open).length;
          const filteredCount = results.filter(
            (r: any) => String(r?.state || '').toLowerCase().trim() === 'filtered'
          ).length;
          return { ...h, results, openCount, filteredCount };
        })
        .sort((a, b) => {
          if (a.openCount > 0 !== b.openCount > 0) return a.openCount > 0 ? -1 : 1;
          if (a.filteredCount > 0 !== b.filteredCount > 0) return a.filteredCount > 0 ? -1 : 1;
          return String(a.host || '').localeCompare(String(b.host || ''));
        });

      return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {hosts.map((h, idx) => {
            const hostKey = h.host || String(idx);
            const isCollapsed = !!collapsedHosts[hostKey];
            if (h.error) {
              return (
                <div
                  key={hostKey}
                  className="host-card bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-3.5"
                >
                  <div className="font-bold text-sm text-[var(--text-primary)]">{h.host}</div>
                  <div className="text-xs text-rose-400 mt-1">Error: {h.error}</div>
                </div>
              );
            }
            const results = h.results || [];
            const openCount = h.openCount || 0;
            const closedCount = results.length - openCount;

            return (
              <div
                key={hostKey}
                className="host-card bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-3.5"
              >
                <div className="host-header flex justify-between items-center">
                  <div className="flex items-center gap-2.5">
                    <button
                      type="button"
                      onClick={() =>
                        setCollapsedHosts((prev) => ({ ...prev, [hostKey]: !prev[hostKey] }))
                      }
                      className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                    >
                      {isCollapsed ? (
                        <ChevronRight className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>
                    <div>
                      <div className="font-bold text-sm text-[var(--text-primary)]">{h.host}</div>
                      <div className="text-xs text-[var(--text-muted)] mt-0.5">
                        Puertos detectados: {results.length} · Abiertos: {openCount} · Cerrados:{' '}
                        {closedCount}
                      </div>
                    </div>
                  </div>
                  {h.duration_seconds && (
                    <div className="text-xs text-[var(--text-muted)]">{h.duration_seconds}s</div>
                  )}
                </div>

                {!isCollapsed && (
                  <div className="host-body mt-3 max-h-48 overflow-y-auto space-y-1.5 pr-1">
                    {results.map((r: any, pIdx: number) => {
                      const rstate = String(r?.state || '').toLowerCase().trim();
                      return (
                        <div
                          key={pIdx}
                          className="port-item flex justify-between items-center px-2.5 py-1.5 rounded-lg bg-[var(--bg-app)]"
                        >
                          <div>
                            <div className="font-bold text-xs text-[var(--text-primary)]">
                              {r.port} · {r.service || ''}
                            </div>
                            <div className="text-[11px] text-[var(--text-muted)]">
                              {r.protocol || 'tcp'} {r.product ? `· ${r.product}` : ''}
                            </div>
                          </div>
                          <div>
                            {rstate === 'filtered' ? (
                              <span className="px-1.5 py-0.5 rounded bg-amber-500 text-white font-semibold text-[10px]">
                                FILTERED
                              </span>
                            ) : r.open ? (
                              <span className="px-1.5 py-0.5 rounded bg-emerald-600 text-white font-semibold text-[10px]">
                                OPEN
                              </span>
                            ) : (
                              <span className="px-1.5 py-0.5 rounded bg-rose-600 text-white font-semibold text-[10px]">
                                CLOSED
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      );
    }

    // 6. unhash & unhash-file
    if (op.id === 'unhash' || op.path === '/hashed/unhash-file') {
      const list: any[] = Array.isArray(resObj)
        ? resObj
        : Array.isArray(resObj?.results)
        ? resObj.results
        : [];
      const foundB64 = resObj?.found_file_b64;
      const foundName = resObj?.found_file_name || 'hashes_encontrados.txt';

      if (list.length > 0) {
        return (
          <div className="space-y-4">
            {foundB64 && (
              <button
                type="button"
                onClick={() => {
                  const blob = new Blob(
                    [Uint8Array.from(atob(foundB64), (c) => c.charCodeAt(0))],
                    { type: 'text/plain' }
                  );
                  const link = document.createElement('a');
                  link.href = URL.createObjectURL(blob);
                  link.download = foundName;
                  document.body.appendChild(link);
                  link.click();
                  setTimeout(() => document.body.removeChild(link), 100);
                }}
                className="btn-download-found px-4 py-2 rounded-xl bg-[var(--brand-primary)] text-white font-semibold text-xs flex items-center gap-2 btn-bounce"
              >
                <FileDown className="w-4 h-4" />
                <span>Descargar resultados encontrados (.txt)</span>
              </button>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {list.map((item, idx) => (
                <div
                  key={idx}
                  className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-4 space-y-1 text-xs"
                >
                  <div className="text-[var(--text-muted)]">Hash:</div>
                  <div className="font-mono break-all text-sm text-[var(--text-primary)] mb-2">
                    {item.hash}
                  </div>
                  <div>
                    <strong>Tipo:</strong>{' '}
                    <span className="text-sky-400">{item.type || '-'}</span>
                  </div>
                  <div>
                    <strong>Resultado:</strong>{' '}
                    <span className={item.found ? 'text-emerald-400 font-semibold' : 'text-rose-400'}>
                      {item.original || 'No encontrado'}
                    </span>
                  </div>
                  <div>
                    <strong>Método:</strong> <span>{item.method || '-'}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      }
    }

    // 7. /hashed/upload-hash-file
    if (op.path === '/hashed/upload-hash-file' && Array.isArray(resObj?.resultados)) {
      return (
        <div className="space-y-4">
          <div className="p-3.5 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] flex flex-wrap gap-6 items-center text-xs">
            <span>
              <strong>Total líneas:</strong> {resObj.total}
            </span>
            <span className="text-emerald-400">
              <strong>Insertados:</strong> {resObj.success}
            </span>
            <span className="text-amber-400">
              <strong>Existentes:</strong> {resObj.existentes}
            </span>
            <span className="text-rose-400">
              <strong>Errores:</strong> {resObj.errores}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {resObj.resultados.map((item: any, idx: number) => {
              const statusStr = String(item.status || '');
              const isExisting = statusStr.includes('ya almacenado');
              const isError =
                statusStr.startsWith('Error') ||
                statusStr.startsWith('Formato') ||
                statusStr.startsWith('Tipo de hash desconocido');
              return (
                <div
                  key={idx}
                  className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-4 flex items-center gap-4 text-xs"
                >
                  <div className="shrink-0">
                    {isExisting ? (
                      <Info className="w-7 h-7 text-amber-400" />
                    ) : isError ? (
                      statusStr.startsWith('Tipo') ? (
                        <HelpCircle className="w-7 h-7 text-rose-400" />
                      ) : (
                        <XCircle className="w-7 h-7 text-rose-400" />
                      )
                    ) : (
                      <CheckCircle2 className="w-7 h-7 text-emerald-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="text-[var(--text-muted)]">
                      Línea: {item.line !== undefined ? item.line : '-'}
                    </div>
                    <div>
                      <strong>Palabra:</strong>{' '}
                      <span className="text-sky-400">{item.palabra ?? '-'}</span>
                    </div>
                    <div className="font-mono break-all">
                      <strong>Hash:</strong> {item.hash ?? '-'}
                    </div>
                    <div>
                      <strong>Método de cifrado:</strong>{' '}
                      <span className="text-sky-300">{item.hash_type ?? '-'}</span>
                    </div>
                    <div>
                      <strong>Estado:</strong>{' '}
                      <span
                        className={`font-semibold ${
                          isExisting
                            ? 'text-amber-400'
                            : isError
                            ? 'text-rose-400'
                            : 'text-emerald-400'
                        }`}
                      >
                        {item.status ?? '-'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    // 8. /hashed/hash-file
    if (op.path === '/hashed/hash-file' && Array.isArray(resObj?.resultados)) {
      const processed = resObj.resultados.filter((x: any) => !x.error).length;
      const errors = resObj.resultados.filter((x: any) => x.error).length;
      return (
        <div className="space-y-4">
          <div className="p-3.5 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] flex flex-wrap gap-6 items-center text-xs">
            <span>
              <strong>Total líneas:</strong> {resObj.total}
            </span>
            <span className="text-emerald-400">
              <strong>Procesadas:</strong> {processed}
            </span>
            <span className="text-rose-400">
              <strong>Errores:</strong> {errors}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {resObj.resultados.map((item: any, idx: number) => (
              <div
                key={idx}
                className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-4 flex items-center gap-4 text-xs"
              >
                <div className="shrink-0">
                  {item.error ? (
                    <XCircle className="w-7 h-7 text-rose-400" />
                  ) : (
                    <Lock className="w-7 h-7 text-emerald-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="text-[var(--text-muted)]">
                    Línea: {item.line !== undefined ? item.line : '-'}
                  </div>
                  <div>
                    <strong>Palabra:</strong>{' '}
                    <span className="text-sky-400">{item.palabra ?? '-'}</span>
                  </div>
                  <div className="font-mono break-all">
                    <strong>Hash:</strong> {item.hash ?? '-'}
                  </div>
                  <div>
                    <strong>Algoritmo:</strong>{' '}
                    <span className="text-sky-300">{item.algorithm ?? '-'}</span>
                  </div>
                  <div>
                    <strong>Estado:</strong>{' '}
                    <span
                      className={`font-semibold ${
                        item.error ? 'text-rose-400' : 'text-emerald-400'
                      }`}
                    >
                      {item.error || 'OK'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // 9. Default two-column response (Friendly + Raw JSON)
    const rawJsonStr =
      typeof state.result === 'string'
        ? state.result
        : JSON.stringify(state.result, null, 2);

    return (
      <div className="response-two-col flex flex-col lg:flex-row gap-4 items-start">
        {/* Left pane: Friendly view */}
        <div className="left-pane flex-1 min-w-0 w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
          <div className="flex justify-between items-center px-4 py-2.5 border-b border-[var(--border-subtle)]">
            <span className="text-xs text-[var(--text-muted)]">
              Status: {state.status || 200}
            </span>
            <button
              type="button"
              onClick={() => setLeftCollapsed(!leftCollapsed)}
              className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            >
              {leftCollapsed ? '▸' : '▾'}
            </button>
          </div>
          {!leftCollapsed && (
            <div className="p-4 overflow-auto">{renderFriendlyValue(state.result)}</div>
          )}
        </div>

        {/* Right pane: Raw JSON */}
        <div className="right-pane w-full lg:w-[420px] shrink-0 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
          <div className="flex justify-between items-center px-4 py-2.5 border-b border-[var(--border-subtle)]">
            <span className="text-xs text-[var(--text-muted)]">JSON crudo</span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setRightCollapsed(!rightCollapsed)}
                className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              >
                {rightCollapsed ? '▸' : '▾'}
              </button>
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard?.writeText(rawJsonStr);
                  showToast('JSON copiado');
                }}
                className="copy-json-btn px-2.5 py-1 rounded-lg bg-[var(--bg-app)] border border-[var(--border-subtle)] text-xs text-sky-300 hover:text-white flex items-center gap-1"
              >
                <Copy className="w-3 h-3" />
                <span>Copiar JSON</span>
              </button>
            </div>
          </div>
          {!rightCollapsed && (
            <div className="p-3 bg-[var(--bg-app)]">
              <pre className="max-h-[480px] overflow-auto text-xs font-mono text-[var(--text-secondary)] whitespace-pre-wrap">
                {rawJsonStr}
              </pre>
            </div>
          )}
        </div>
      </div>
    );
  };

  /**
   * @brief Render a single controller section in the left controllers pane.
   */
  const renderControllerSection = (name: string) => {
    const ops = CONTROLLERS[name] || [];
    const isCollapsed = !!collapsedSections[name];
    const SectionIcon = getControllerIcon(name);

    return (
      <div key={name} className={`controller-section mb-1.5 ${isCollapsed ? 'collapsed' : ''}`}>
        <button
          type="button"
          onClick={() => toggleSection(name)}
          className="controller-header w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold text-[var(--text-primary)] hover:bg-[var(--bg-surface-subtle)] transition-all"
        >
          <span className="flex items-center gap-2">
            <SectionIcon className="w-4 h-4 text-[var(--brand-primary)]" />
            <span>{name}</span>
          </span>
          {isCollapsed ? (
            <ChevronRight className="w-3.5 h-3.5 text-[var(--text-muted)]" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-[var(--text-muted)]" />
          )}
        </button>

        {!isCollapsed && (
          <div className="ops-container pl-3 pr-1 py-1 space-y-1">
            {ops.map((op) => {
              const OpIcon = getOperationIcon(op.title);
              const isSelected = selectedOp?.id === op.id;
              return (
                <button
                  key={op.id}
                  type="button"
                  data-op-id={op.id}
                  onClick={() => handleSelectOp(name, op)}
                  className={`op-btn w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs text-left transition-all btn-bounce ${
                    isSelected
                      ? 'active bg-[var(--brand-primary)] text-white font-semibold shadow-sm'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)]/50'
                  }`}
                >
                  <OpIcon
                    className={`w-3.5 h-3.5 shrink-0 ${
                      isSelected ? 'text-white' : 'text-[var(--brand-primary)]'
                    }`}
                  />
                  <span className="truncate">{op.title}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  const currentOpState = selectedOp ? getOpState(selectedOp) : null;

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left: Controllers list inside the fastapi view */}
      <div className="controllers-pane w-72 bg-[var(--bg-surface)] border-r border-[var(--border-subtle)] p-4 overflow-y-auto shrink-0 select-none">
        <h3 className="font-bold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
          <Zap className="w-4 h-4 text-[var(--brand-primary)]" />
          <span>Services</span>
        </h3>

        <div id="controllers-list" className="space-y-1">
          {/* OSINT Category at top (collapsed by default) */}
          <div className={`controller-category mb-2 ${osintCollapsed ? 'collapsed' : ''}`}>
            <button
              type="button"
              onClick={() => setOsintCollapsed(!osintCollapsed)}
              className="controller-category-header w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold text-[var(--brand-primary)] bg-[var(--brand-primary)]/5 hover:bg-[var(--brand-primary)]/10 transition-all"
            >
              <span className="flex items-center gap-2">
                <Globe className="w-4 h-4" />
                <span>OSINT</span>
              </span>
              {osintCollapsed ? (
                <ChevronRight className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
            </button>

            {!osintCollapsed && (
              <div className="controller-category-inner pl-2 pt-1.5 space-y-1 border-l border-[var(--border-subtle)] ml-2 mt-1">
                {OSINT_CONTROLLERS.map((name) => renderControllerSection(name))}
              </div>
            )}
          </div>

          {/* Remaining Controller Sections */}
          {MAIN_CONTROLLERS.map((name) => renderControllerSection(name))}
        </div>
      </div>

      {/* Right: Operation form and result */}
      <div className="op-area flex-1 p-6 flex flex-col overflow-y-auto">
        <div className="mb-4 flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
          <h3 id="op-title" className="font-bold text-base text-[var(--text-primary)] m-0">
            {selectedOp && selectedController
              ? `${selectedController} — ${selectedOp.title} (${selectedOp.method})`
              : 'Seleccione una operación'}
          </h3>
          <div className="text-xs text-[var(--text-muted)]">
            FastAPI API: <code className="text-[var(--brand-primary)]">http://127.0.0.1:8000</code>
          </div>
        </div>

        {/* Form Area */}
        <div id="op-form" className="mb-6">
          {!selectedOp ? (
            <p className="text-xs text-[var(--text-muted)]">
              Seleccione una operación en la izquierda para ver los parámetros y ejecutarla.
            </p>
          ) : selectedOp.path === '/status' ? (
            /* Special interactive Status & Workers panel */
            <div className="space-y-4">
              <div className="text-xs text-[var(--text-secondary)]">
                <strong className="text-[var(--brand-primary)] mr-2">{selectedOp.method}</strong>
                <span>{selectedOp.desc}</span>
              </div>

              <div className="flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={fetchSystemStatus}
                  disabled={statusLoading}
                  className="px-3.5 py-2 rounded-xl bg-[var(--brand-primary)] text-white text-xs font-semibold flex items-center gap-1.5 btn-bounce"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${statusLoading ? 'animate-spin' : ''}`} />
                  <span>Actualizar estado</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleToggleAllWorkers(true)}
                  disabled={statusLoading}
                  className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 btn-bounce"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Start All</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleToggleAllWorkers(false)}
                  disabled={statusLoading}
                  className="px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center gap-1.5 btn-bounce"
                >
                  <XCircle className="w-3.5 h-3.5" />
                  <span>Stop All</span>
                </button>
              </div>

              <div
                id="op-status-box"
                className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 space-y-3"
              >
                {!statusData ? (
                  <div className="text-xs text-[var(--text-muted)]">Cargando...</div>
                ) : (
                  <>
                    <div className="text-xs">
                      <strong>Infra:</strong>{' '}
                      {statusData.infra_ready ? (
                        <span className="text-emerald-400 font-semibold">OK</span>
                      ) : (
                        <span className="text-rose-400 font-semibold">NO</span>
                      )}
                      {statusData.infra_error && (
                        <em className="text-rose-400 ml-2">{statusData.infra_error}</em>
                      )}
                    </div>
                    <div className="text-xs">
                      <strong>UI initialized:</strong>{' '}
                      {statusData.ui_initialized ? (
                        <span className="text-emerald-400 font-semibold">sí</span>
                      ) : (
                        <span className="text-rose-400 font-semibold">no</span>
                      )}
                    </div>

                    <div className="pt-2">
                      <strong className="text-xs block mb-2.5">Workers</strong>
                      <div id="workers-control-list" className="space-y-2">
                        {Object.entries(statusData.workers || {}).map(([name, val]) => {
                          const friendly = WORKER_FRIENDLY[name] || { name, info: '' };
                          const isRunning = Boolean(val);
                          return (
                            <div
                              key={name}
                              className="flex items-center justify-between gap-4 p-3 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)]"
                            >
                              <div>
                                <div className="font-semibold text-xs text-[var(--text-primary)] flex items-center gap-1.5">
                                  <span>{friendly.name}</span>
                                  {friendly.info && (
                                    <span title={friendly.info} className="cursor-help text-sky-400">
                                      <Info className="w-3.5 h-3.5" />
                                    </span>
                                  )}
                                </div>
                                <div className="text-[11px] text-[var(--text-muted)] mt-0.5">
                                  Status:{' '}
                                  {isRunning ? (
                                    <span className="text-emerald-400 font-semibold">running</span>
                                  ) : (
                                    <span className="text-rose-400 font-semibold">stopped</span>
                                  )}
                                </div>
                              </div>

                              <button
                                type="button"
                                data-worker-toggle={name}
                                data-enabled={String(isRunning)}
                                disabled={togglingWorker === name}
                                onClick={() => handleToggleWorker(name, isRunning)}
                                className={`px-3 py-1.5 rounded-lg text-xs font-semibold text-white transition-all btn-bounce ${
                                  isRunning
                                    ? 'bg-rose-600 hover:bg-rose-500'
                                    : 'bg-emerald-600 hover:bg-emerald-500'
                                } disabled:opacity-50`}
                              >
                                {isRunning ? 'Stop' : 'Activate'}
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          ) : (
            /* Standard & Custom Operation Form */
            <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5">
              <div className="mb-4">
                <span className="px-2 py-0.5 rounded bg-[var(--brand-primary)]/15 text-[var(--brand-primary)] font-bold text-xs mr-2">
                  {selectedOp.method}
                </span>
                <span className="text-xs font-mono text-[var(--text-muted)]">{selectedOp.path}</span>
                {selectedOp.desc && (
                  <div className="text-xs text-[var(--text-secondary)] mt-2">{selectedOp.desc}</div>
                )}
              </div>

              <form onSubmit={(e) => handleSubmitOp(e, selectedOp)} className="space-y-4">
                {selectedOp.params.map((p) => {
                  const val = currentOpState?.values[p.name] ?? '';

                  if (p.type === 'file') {
                    return (
                      <div key={p.name} className="space-y-1.5">
                        <label className="block text-xs font-semibold text-[var(--text-secondary)]">
                          {p.label || p.name}
                        </label>
                        <label
                          onDragOver={(e) => e.preventDefault()}
                          onDrop={(e) => {
                            e.preventDefault();
                            const f = e.dataTransfer.files?.[0];
                            if (f) {
                              updateOpState(selectedOp.id, (prev) => ({
                                ...prev,
                                file: f,
                                error: null,
                              }));
                            }
                          }}
                          className="file-drop-zone flex flex-col items-center justify-center p-5 border-2 border-dashed border-[var(--brand-primary)]/50 rounded-xl bg-[var(--bg-surface-subtle)] hover:bg-[var(--brand-primary)]/5 text-center cursor-pointer transition-all"
                        >
                          <Upload className="w-5 h-5 text-[var(--brand-primary)] mb-1.5" />
                          <span className="text-xs font-medium text-[var(--brand-primary)]">
                            {currentOpState?.file
                              ? `Archivo seleccionado: ${currentOpState.file.name}`
                              : 'Arrastra aquí el archivo o haz clic para seleccionar'}
                          </span>
                          <input
                            type="file"
                            name={p.name}
                            accept={p.accept}
                            className="hidden"
                            onChange={(e) => {
                              const f = e.target.files?.[0] || null;
                              updateOpState(selectedOp.id, (prev) => ({
                                ...prev,
                                file: f,
                                error: null,
                              }));
                            }}
                          />
                        </label>
                      </div>
                    );
                  }

                  if (p.type === 'enum' && Array.isArray(p.options)) {
                    return (
                      <div key={p.name} className="space-y-1.5">
                        <label className="block text-xs font-semibold text-[var(--text-secondary)]">
                          {p.label || p.name}
                        </label>
                        <select
                          name={p.name}
                          value={String(val)}
                          onChange={(e) =>
                            updateOpState(selectedOp.id, (prev) => ({
                              ...prev,
                              values: { ...prev.values, [p.name]: e.target.value },
                            }))
                          }
                          className="w-full bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-xl px-3 py-2 text-xs text-[var(--text-primary)]"
                        >
                          {p.options.map((opt) => (
                            <option key={opt} value={opt}>
                              {opt}
                            </option>
                          ))}
                        </select>
                      </div>
                    );
                  }

                  if (p.type === 'textarea') {
                    return (
                      <div key={p.name} className="space-y-1.5">
                        <label className="block text-xs font-semibold text-[var(--text-secondary)]">
                          {p.label || p.name}
                        </label>
                        <textarea
                          name={p.name}
                          rows={p.large ? 8 : 5}
                          required
                          placeholder={p.placeholder || ''}
                          value={String(val)}
                          onChange={(e) =>
                            updateOpState(selectedOp.id, (prev) => ({
                              ...prev,
                              values: { ...prev.values, [p.name]: e.target.value },
                            }))
                          }
                          className="w-full bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-xl p-3 font-mono text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand-primary)]"
                        />
                      </div>
                    );
                  }

                  if (p.type === 'checkbox') {
                    return (
                      <label
                        key={p.name}
                        className="flex items-center gap-2 text-xs font-medium text-[var(--text-secondary)] cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          name={p.name}
                          checked={Boolean(val)}
                          onChange={(e) =>
                            updateOpState(selectedOp.id, (prev) => ({
                              ...prev,
                              values: { ...prev.values, [p.name]: e.target.checked },
                            }))
                          }
                          className="rounded text-[var(--brand-primary)]"
                        />
                        <span>{p.label || p.name}</span>
                      </label>
                    );
                  }

                  if (p.type === 'number') {
                    return (
                      <div key={p.name} className="space-y-1.5">
                        <label className="block text-xs font-semibold text-[var(--text-secondary)]">
                          {p.label || p.name}
                        </label>
                        <input
                          type="number"
                          name={p.name}
                          min={1}
                          max={20}
                          placeholder={p.placeholder || ''}
                          value={String(val)}
                          onChange={(e) =>
                            updateOpState(selectedOp.id, (prev) => ({
                              ...prev,
                              values: { ...prev.values, [p.name]: e.target.value },
                            }))
                          }
                          className="w-36 bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-xl px-3 py-2 text-xs text-[var(--text-primary)]"
                        />
                      </div>
                    );
                  }

                  return (
                    <div key={p.name} className="space-y-1.5">
                      <label className="block text-xs font-semibold text-[var(--text-secondary)]">
                        {p.label || p.name}
                      </label>
                      <input
                        type="text"
                        name={p.name}
                        placeholder={p.placeholder || ''}
                        value={String(val)}
                        onChange={(e) =>
                          updateOpState(selectedOp.id, (prev) => ({
                            ...prev,
                            values: { ...prev.values, [p.name]: e.target.value },
                          }))
                        }
                        className="w-full bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-xl px-3 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--brand-primary)]"
                      />
                    </div>
                  );
                })}

                <div className="flex items-center gap-2.5 pt-2">
                  <button
                    type="submit"
                    disabled={currentOpState?.loading}
                    className="exec-btn px-4 py-2 rounded-xl bg-[var(--brand-primary)] text-white font-semibold text-xs flex items-center gap-1.5 hover:bg-[var(--brand-primary-hover)] transition-all btn-bounce shadow-md disabled:opacity-50"
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>Ejecutar</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleClearFormAndResult(selectedOp)}
                    className="clear-btn px-4 py-2 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] font-semibold text-xs flex items-center gap-1.5 transition-all btn-bounce"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Limpiar</span>
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>

        {/* Result Area */}
        {selectedOp && selectedOp.path !== '/status' && currentOpState && (
          <div
            id="op-result"
            className="flex-1 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 overflow-auto"
          >
            {renderOperationResult(selectedOp, currentOpState)}
          </div>
        )}
      </div>

      {/* Toast Notification */}
      {toastMsg && (
        <div className="fixed right-6 bottom-6 z-50 px-4 py-2.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--brand-primary)]/40 text-xs font-semibold text-[var(--text-primary)] shadow-2xl">
          {toastMsg}
        </div>
      )}
    </div>
  );
};
