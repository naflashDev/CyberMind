/**
 * @file ConfigView.tsx
 * @author naflashDev
 * @brief Vista de configuración del sistema y personalización visual.
 * @details Permite alternar paletas cromáticas y tipografías de la Guía de Diseño Transversal de naflashDev, así como editar los ficheros .ini del backend.
 */

import React, { useEffect, useState } from 'react';
import { Palette, Type, Sliders, Save, CheckCircle, RefreshCw } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { FONTS, PALETTES } from '../types/theme';
import { api } from '../services/api';

export const ConfigView: React.FC = () => {
  const { palette, setPalette, font, setFont, mode, setMode } = useTheme();

  // Estado de ficheros .ini
  const [iniFiles, setIniFiles] = useState<{ name: string; content: string }[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [fileContent, setFileContent] = useState<string>('');
  const [loadingIni, setLoadingIni] = useState(false);
  const [savingStatus, setSavingStatus] = useState<string | null>(null);

  useEffect(() => {
    loadConfigFiles();
  }, []);

  const loadConfigFiles = async () => {
    setLoadingIni(true);
    try {
      const res = await api.getConfigFiles();
      if (res.files && res.files.length > 0) {
        setIniFiles(res.files);
        setSelectedFile(res.files[0].name);
        setFileContent(res.files[0].content);
      }
    } catch (e) {
      console.error('Error cargando ficheros de config:', e);
    } finally {
      setLoadingIni(false);
    }
  };

  const handleSelectFile = (name: string) => {
    setSelectedFile(name);
    const f = iniFiles.find((x) => x.name === name);
    if (f) setFileContent(f.content);
  };

  const handleSaveConfig = async () => {
    if (!selectedFile) return;
    setSavingStatus('Guardando...');
    try {
      await api.saveConfigFile(selectedFile, fileContent);
      setSavingStatus('¡Guardado con éxito!');
      setTimeout(() => setSavingStatus(null), 3000);
    } catch (e) {
      setSavingStatus(`Error: ${(e as Error).message}`);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8 animate-fadeIn">
      {/* SECCIÓN 1: SISTEMA DE DISEÑO & APARIENCIA */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xl">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[var(--border-subtle)]">
          <Palette className="w-6 h-6 text-[var(--brand-primary)]" />
          <div>
            <h2 className="text-lg font-bold text-[var(--text-primary)]">Sistema de Diseño & Apariencia</h2>
            <p className="text-xs text-[var(--text-secondary)]">Personaliza la identidad visual y ergonomía conforme a la Guía Transversal de naflashDev</p>
          </div>
        </div>

        {/* 1.1 Paleta Cromática */}
        <div className="mb-8">
          <label className="block text-sm font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
            <span>Paleta Cromática Canónica</span>
            <span className="text-[10px] font-normal px-2 py-0.5 rounded-full bg-[var(--brand-primary)]/10 text-[var(--brand-primary)] border border-[var(--brand-primary)]/20">
              6 Temas
            </span>
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {PALETTES.map((p) => {
              const isSelected = palette === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => setPalette(p.id)}
                  className={`p-4 rounded-xl border text-left transition-all btn-bounce ${
                    isSelected
                      ? 'border-[var(--brand-primary)] bg-[var(--brand-primary)]/5 ring-2 ring-[var(--brand-primary)]/20'
                      : 'border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)] hover:border-[var(--border-strong)]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm text-[var(--text-primary)]">{p.name}</span>
                    <span className="w-4 h-4 rounded-full border border-white/20" style={{ backgroundColor: p.primary }} />
                  </div>
                  <p className="text-xs text-[var(--text-muted)] line-clamp-2">{p.desc}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* 1.2 Tipografía Primaria */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
            <Type className="w-4 h-4 text-[var(--brand-primary)]" />
            <span>Familia Tipográfica Primaria</span>
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {FONTS.map((f) => {
              const isSelected = font === f.id;
              return (
                <button
                  key={f.id}
                  onClick={() => setFont(f.id)}
                  className={`p-3.5 rounded-xl border text-left transition-all btn-bounce ${
                    isSelected
                      ? 'border-[var(--brand-primary)] bg-[var(--brand-primary)]/5 ring-2 ring-[var(--brand-primary)]/20'
                      : 'border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)] hover:border-[var(--border-strong)]'
                  }`}
                >
                  <div className="font-medium text-sm text-[var(--text-primary)]">{f.name}</div>
                  <div className="text-[11px] text-[var(--text-muted)]">{f.category}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* 1.3 Modo Oscuro / Modo Claro */}
        <div className="pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between">
          <div>
            <span className="text-sm font-semibold text-[var(--text-primary)] block">Contraste de Superficie</span>
            <span className="text-xs text-[var(--text-muted)]">Alterna entre modo oscuro (Dark-First) y modo claro de alto contraste</span>
          </div>
          <div className="flex items-center gap-2 bg-[var(--bg-surface-subtle)] p-1 rounded-xl border border-[var(--border-subtle)]">
            <button
              onClick={() => setMode('dark')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                mode === 'dark' ? 'bg-[var(--brand-primary)] text-white' : 'text-[var(--text-secondary)]'
              }`}
            >
              Oscuro
            </button>
            <button
              onClick={() => setMode('light')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                mode === 'light' ? 'bg-[var(--brand-primary)] text-white' : 'text-[var(--text-secondary)]'
              }`}
            >
              Claro
            </button>
          </div>
        </div>
      </div>

      {/* SECCIÓN 2: CONFIGURACIÓN DE ARCHIVOS DEL SISTEMA (.INI) */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-3">
            <Sliders className="w-6 h-6 text-[var(--brand-primary)]" />
            <div>
              <h2 className="text-lg font-bold text-[var(--text-primary)]">Parámetros del Backend (.ini)</h2>
              <p className="text-xs text-[var(--text-secondary)]">Edición directa de directivas de scraping, Ollama y servicios</p>
            </div>
          </div>
          <button
            onClick={loadConfigFiles}
            className="p-2 rounded-xl border border-[var(--border-subtle)] hover:bg-[var(--bg-surface-subtle)] text-[var(--text-secondary)] transition-all btn-bounce"
            title="Recargar archivos"
          >
            <RefreshCw className={`w-4 h-4 ${loadingIni ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Selector de archivos .ini */}
        <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
          {iniFiles.map((f) => (
            <button
              key={f.name}
              onClick={() => handleSelectFile(f.name)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all btn-bounce ${
                selectedFile === f.name
                  ? 'bg-[var(--brand-primary)] text-white shadow-md'
                  : 'bg-[var(--bg-surface-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)]'
              }`}
            >
              {f.name}
            </button>
          ))}
        </div>

        {/* Editor de texto */}
        <div className="relative">
          <textarea
            value={fileContent}
            onChange={(e) => setFileContent(e.target.value)}
            className="w-full h-80 p-4 rounded-xl font-mono text-xs bg-[var(--bg-app)] text-[var(--text-primary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--brand-primary)] transition-colors resize-y"
            placeholder="Contenido del archivo .ini..."
          />
        </div>

        {/* Acciones */}
        <div className="mt-4 flex items-center justify-between">
          <div className="text-xs font-medium text-[var(--text-muted)]">
            {savingStatus && (
              <span className="flex items-center gap-1.5 text-emerald-400">
                <CheckCircle className="w-4 h-4" />
                {savingStatus}
              </span>
            )}
          </div>
          <button
            onClick={handleSaveConfig}
            className="px-5 py-2.5 rounded-xl bg-[var(--brand-primary)] text-white font-semibold text-xs flex items-center gap-2 hover:bg-[var(--brand-primary-hover)] transition-all btn-bounce shadow-lg shadow-[var(--brand-primary)]/20"
          >
            <Save className="w-4 h-4" />
            <span>Guardar Configuración</span>
          </button>
        </div>
      </div>
    </div>
  );
};
