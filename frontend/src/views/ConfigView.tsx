/**
 * @file ConfigView.tsx
 * @author naflashDev
 * @brief Exact functional replication of the system configuration view (view-config) from index.html and ui.js with modern Lucide icons.
 * @details Loads and saves .ini parameter blocks via GET /config and POST /config with friendly names, tooltips,
 *          boolean toggles, and discard support, plus visual theme customization.
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  Sliders,
  Save,
  Trash2,
  Info,
  Check,
  X,
  Palette,
  Type,
  Wrench,
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { FONTS, PALETTES } from '../types/theme';
import { api, type ConfigFileBlock } from '../services/api';

const CONFIG_FRIENDLY_NAMES: Record<string, string> = {
  use_ollama: 'Activar IA CyberSentinel',
  host: 'Dirección del servidor',
  ports: 'Puertos a escanear',
  concurrency: 'Concurrencia de escaneo',
  cidr: 'Rango de red (CIDR)',
  start: 'IP de inicio',
  end: 'IP de fin',
  distro_name: 'Nombre distribución',
  dockers_name: 'Nombre contenedores',
  server_ip: 'IP servidor',
  server_port: 'Puerto servidor',
};

const CONFIG_HINTS: Record<string, string> = {
  distro_name:
    'Ejemplo: Ubuntu, Debian, Windows. Indica el sistema operativo principal.',
  dockers_name:
    'Lista separada por comas de los nombres de los contenedores Docker. Ejemplo: app1,db1,nginx.',
  use_ollama: 'Activa la IA CyberSentinel si está disponible en el sistema.',
  server_ip:
    'Dirección IP o nombre DNS del servidor. Ejemplo: localhost, 192.168.1.10.',
  server_port: 'Puerto de conexión del servidor. Ejemplo: 9200.',
  host: 'IP o nombre del host a escanear. Ejemplo: 192.168.1.1 o example.com.',
  ports: 'Puertos separados por comas. Ejemplo: 80,443,8080.',
  concurrency: 'Número de procesos simultáneos para el escaneo. Ejemplo: 20.',
  cidr: 'Rango de red en formato CIDR. Ejemplo: 192.168.1.0/24.',
  start: 'IP de inicio del rango. Ejemplo: 192.168.1.1.',
  end: 'IP final del rango. Ejemplo: 192.168.1.254. Opcional.',
};

interface ConfigViewProps {
  isActive?: boolean;
  onConfigSaved?: () => void;
}

export const ConfigView: React.FC<ConfigViewProps> = ({
  isActive,
  onConfigSaved,
}) => {
  const { palette, setPalette, font, setFont, mode, setMode } = useTheme();

  const [originalFiles, setOriginalFiles] = useState<ConfigFileBlock[]>([]);
  const [configCache, setConfigCache] = useState<ConfigFileBlock[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [configStatus, setConfigStatus] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  /**
   * @brief Fetch configuration files from GET /config and clone into editable cache.
   */
  const loadConfigFiles = useCallback(async () => {
    setConfigStatus('');
    setErrorMsg(null);
    setLoading(true);
    try {
      const data = await api.getConfig();
      const files = Array.isArray(data?.files) ? data.files : [];
      setOriginalFiles(JSON.parse(JSON.stringify(files)));
      setConfigCache(JSON.parse(JSON.stringify(files)));
    } catch {
      setErrorMsg('Error cargando configuración');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfigFiles();
  }, [loadConfigFiles]);

  useEffect(() => {
    if (isActive) {
      loadConfigFiles();
    }
  }, [isActive, loadConfigFiles]);

  const handleToggleBoolean = (fileIdx: number, paramIdx: number) => {
    setConfigCache((prev) => {
      const next = JSON.parse(JSON.stringify(prev)) as ConfigFileBlock[];
      const currentVal = String(next[fileIdx].params[paramIdx].value).toLowerCase();
      next[fileIdx].params[paramIdx].value = currentVal === 'true' ? 'false' : 'true';
      return next;
    });
  };

  const handleParamChange = (fileIdx: number, paramIdx: number, newValue: string) => {
    setConfigCache((prev) => {
      const next = JSON.parse(JSON.stringify(prev)) as ConfigFileBlock[];
      next[fileIdx].params[paramIdx].value = newValue;
      return next;
    });
  };

  /**
   * @brief Save all modified .ini blocks via POST /config and trigger CyberSentinel visibility refresh.
   */
  const handleSaveConfig = async () => {
    setConfigStatus('');
    setSaving(true);
    try {
      for (const fileObj of configCache) {
        await api.saveConfigFile(fileObj.file, fileObj.params);
      }
      setConfigStatus('¡Configuración guardada!');
      await loadConfigFiles();
      setConfigStatus('¡Configuración guardada!');
      if (onConfigSaved) {
        onConfigSaved();
      }
    } catch (e) {
      setConfigStatus(`Error al guardar: ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  };

  /**
   * @brief Discard unsaved changes and restore from original snapshot.
   */
  const handleDiscardConfig = () => {
    setConfigCache(JSON.parse(JSON.stringify(originalFiles)));
    setConfigStatus('Cambios descartados.');
  };

  return (
    <div className="h-full overflow-y-auto p-6 space-y-8">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* SECTION 1: SYSTEM CONFIGURATION (.INI FILES) */}
        <div className="config-panel bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xl">
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[var(--border-subtle)]">
            <Sliders className="w-6 h-6 text-[var(--brand-primary)]" />
            <h2 className="config-title text-lg font-bold text-[var(--text-primary)] m-0">
              Configuración del sistema
            </h2>
          </div>

          <div id="config-files" className="space-y-5">
            {loading ? (
              <div className="text-xs text-[var(--text-muted)]">
                Cargando configuración...
              </div>
            ) : errorMsg ? (
              <div className="text-xs text-rose-400">{errorMsg}</div>
            ) : (
              configCache.map((fileObj, fileIdx) => {
                let blockName = fileObj.file;
                if (fileObj.file === 'cfg_services.ini') {
                  blockName = 'Configuración servicios';
                } else if (fileObj.file === 'cfg.ini') {
                  blockName = 'Configuración general';
                }

                return (
                  <div
                    key={fileObj.file}
                    className="config-file-block bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-5 space-y-3"
                  >
                    <h3 className="text-sm font-bold text-sky-400 flex items-center gap-2 mb-3">
                      <Wrench className="w-4 h-4 text-[var(--brand-primary)]" />
                      <span>{blockName}</span>
                    </h3>

                    <div className="space-y-3">
                      {fileObj.params.map((p, paramIdx) => {
                        const friendlyLabel = CONFIG_FRIENDLY_NAMES[p.key] || p.key;
                        const hint = CONFIG_HINTS[p.key];
                        const isBool = p.type === 'boolean';
                        const isTrue = String(p.value).toLowerCase() === 'true';

                        return (
                          <div
                            key={p.key}
                            className="config-param-row flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4"
                          >
                            <label className="min-w-[220px] text-xs font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
                              <span>{friendlyLabel}</span>
                              {hint && (
                                <span
                                  title={hint}
                                  className="info-icon cursor-help text-sky-400 inline-flex items-center"
                                >
                                  <Info className="w-3.5 h-3.5" />
                                </span>
                              )}
                            </label>

                            {isBool ? (
                              <button
                                type="button"
                                onClick={() => handleToggleBoolean(fileIdx, paramIdx)}
                                className={`config-toggle-btn px-4 py-1.5 rounded-lg text-xs font-semibold text-white flex items-center gap-1.5 transition-all btn-bounce w-fit ${
                                  isTrue
                                    ? 'bg-emerald-600 hover:bg-emerald-500'
                                    : 'bg-rose-600 hover:bg-rose-500'
                                }`}
                              >
                                {isTrue ? (
                                  <>
                                    <Check className="w-3.5 h-3.5" />
                                    <span>Sí</span>
                                  </>
                                ) : (
                                  <>
                                    <X className="w-3.5 h-3.5" />
                                    <span>No</span>
                                  </>
                                )}
                              </button>
                            ) : (
                              <textarea
                                value={p.value}
                                rows={1}
                                onChange={(e) =>
                                  handleParamChange(fileIdx, paramIdx, e.target.value)
                                }
                                className="flex-1 max-w-md px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-app)] text-xs text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--brand-primary)] resize-y min-h-[32px]"
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Actions */}
          <div className="config-actions flex items-center gap-3 mt-6 pt-4 border-t border-[var(--border-subtle)]">
            <button
              id="btn-save-config"
              type="button"
              disabled={saving}
              onClick={handleSaveConfig}
              className="config-btn-save px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-2 transition-all btn-bounce shadow-md disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>Guardar</span>
            </button>
            <button
              id="btn-discard-config"
              type="button"
              onClick={handleDiscardConfig}
              className="config-btn-discard px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs flex items-center gap-2 transition-all btn-bounce shadow-md"
            >
              <Trash2 className="w-4 h-4" />
              <span>Descartar</span>
            </button>
            <span
              id="config-status"
              className="config-status text-xs font-semibold text-[var(--text-secondary)] ml-2"
            >
              {configStatus}
            </span>
          </div>
        </div>

        {/* SECTION 2: VISUAL DESIGN & THEME CUSTOMIZATION */}
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xl">
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[var(--border-subtle)]">
            <Palette className="w-6 h-6 text-[var(--brand-primary)]" />
            <div>
              <h2 className="text-base font-bold text-[var(--text-primary)] m-0">
                Apariencia y Tema Visual
              </h2>
              <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                Personalización estética de paletas cromáticas, tipografía y modo de contraste
              </p>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-xs font-semibold text-[var(--text-primary)] mb-2.5">
              Paleta Cromática
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {PALETTES.map((p) => {
                const isSelected = palette === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setPalette(p.id)}
                    className={`p-3.5 rounded-xl border text-left transition-all btn-bounce ${
                      isSelected
                        ? 'border-[var(--brand-primary)] bg-[var(--brand-primary)]/10'
                        : 'border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)]'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-xs text-[var(--text-primary)]">
                        {p.name}
                      </span>
                      <span
                        className="w-3.5 h-3.5 rounded-full border border-white/20"
                        style={{ backgroundColor: p.primary }}
                      />
                    </div>
                    <p className="text-[11px] text-[var(--text-muted)] line-clamp-2 m-0">
                      {p.desc}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-xs font-semibold text-[var(--text-primary)] mb-2.5 flex items-center gap-1.5">
              <Type className="w-3.5 h-3.5 text-[var(--brand-primary)]" />
              <span>Tipografía</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {FONTS.map((f) => {
                const isSelected = font === f.id;
                return (
                  <button
                    key={f.id}
                    type="button"
                    onClick={() => setFont(f.id)}
                    className={`p-3 rounded-xl border text-left transition-all btn-bounce ${
                      isSelected
                        ? 'border-[var(--brand-primary)] bg-[var(--brand-primary)]/10'
                        : 'border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)]'
                    }`}
                  >
                    <div className="font-medium text-xs text-[var(--text-primary)]">
                      {f.name}
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)]">{f.category}</div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between">
            <span className="text-xs font-semibold text-[var(--text-primary)]">
              Modo de Contraste
            </span>
            <div className="flex items-center gap-2 bg-[var(--bg-surface-subtle)] p-1 rounded-xl border border-[var(--border-subtle)]">
              <button
                type="button"
                onClick={() => setMode('dark')}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                  mode === 'dark'
                    ? 'bg-[var(--brand-primary)] text-white'
                    : 'text-[var(--text-secondary)]'
                }`}
              >
                Oscuro
              </button>
              <button
                type="button"
                onClick={() => setMode('light')}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                  mode === 'light'
                    ? 'bg-[var(--brand-primary)] text-white'
                    : 'text-[var(--text-secondary)]'
                }`}
              >
                Claro
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
