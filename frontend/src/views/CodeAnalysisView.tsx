/**
 * @file CodeAnalysisView.tsx
 * @author naflashDev
 * @brief Interfaz de análisis SAST de código fuente (texto directo o subida de ficheros/ZIP).
 */

import React, { useState } from 'react';
import { Code, Upload, ShieldAlert, FileDown, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

export const CodeAnalysisView: React.FC = () => {
  const [codeText, setCodeText] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [pdfBase64, setPdfBase64] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleScanText = async () => {
    if (!codeText.trim()) return;
    setAnalyzing(true);
    setErrorMsg(null);
    try {
      const res = await api.scanCodeText(codeText);
      setResults(res.vulnerabilities || []);
      setPdfBase64(res.pdf_base64 || null);
    } catch (e) {
      setErrorMsg((e as Error).message);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleScanFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setAnalyzing(true);
    setErrorMsg(null);
    try {
      const res = await api.scanCodeFile(formData);
      setResults(res.vulnerabilities || []);
      setPdfBase64(res.pdf_base64 || null);
    } catch (e) {
      setErrorMsg((e as Error).message);
    } finally {
      setAnalyzing(false);
    }
  };

  const downloadPdf = () => {
    if (!pdfBase64) return;
    const link = document.createElement('a');
    link.href = `data:application/pdf;base64,${pdfBase64}`;
    link.download = `CyberMind_SAST_Report_${new Date().toISOString().slice(0, 10)}.pdf`;
    link.click();
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between pb-4 border-b border-[var(--border-subtle)] mb-6">
          <div className="flex items-center gap-3">
            <Code className="w-6 h-6 text-[var(--brand-primary)]" />
            <div>
              <h2 className="text-lg font-bold text-[var(--text-primary)]">Análisis SAST de Seguridad en Código</h2>
              <p className="text-xs text-[var(--text-secondary)]">
                Detección heurística multilinguaje (Python Bandit, Go Gosec, C/C++ Flawfinder) con explicaciones asistidas por CyberSentinel
              </p>
            </div>
          </div>

          <label className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--bg-surface-subtle)] hover:bg-[var(--border-subtle)] border border-[var(--border-subtle)] text-[var(--text-primary)] cursor-pointer btn-bounce">
            <Upload className="w-4 h-4 text-[var(--brand-primary)]" />
            <span>Subir Archivo / ZIP</span>
            <input type="file" onChange={handleScanFile} className="hidden" />
          </label>
        </div>

        {/* Input de código en texto */}
        <div className="space-y-4">
          <textarea
            value={codeText}
            onChange={(e) => setCodeText(e.target.value)}
            placeholder="Pega aquí el código fuente para analizar vulnerabilidades (ej. scripts Python, Go, C/C++)..."
            className="w-full h-56 p-4 rounded-xl font-mono text-xs bg-[var(--bg-app)] text-[var(--text-primary)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--brand-primary)]"
          />

          <div className="flex items-center justify-between">
            {errorMsg ? <span className="text-xs text-rose-400">{errorMsg}</span> : <div />}
            <button
              onClick={handleScanText}
              disabled={analyzing || !codeText.trim()}
              className="px-5 py-2.5 rounded-xl bg-[var(--brand-primary)] text-white font-semibold text-xs flex items-center gap-2 hover:bg-[var(--brand-primary-hover)] disabled:opacity-50 transition-all btn-bounce shadow-lg shadow-[var(--brand-primary)]/20"
            >
              <ShieldAlert className="w-4 h-4" />
              <span>{analyzing ? 'Analizando Código...' : 'Iniciar Escaneo SAST'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* RESULTADOS DEL ANÁLISIS */}
      {results.length > 0 && (
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              <h3 className="text-sm font-bold text-[var(--text-primary)]">
                Vulnerabilidades Detectadas ({results.length})
              </h3>
            </div>
            {pdfBase64 && (
              <button
                onClick={downloadPdf}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20 btn-bounce"
              >
                <FileDown className="w-4 h-4" />
                <span>Descargar Informe PDF</span>
              </button>
            )}
          </div>

          <div className="space-y-3">
            {results.map((r, i) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)] flex flex-col gap-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-[var(--brand-primary)]">
                    {r.filename || 'input_code'}:{r.line || '-'}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                      String(r.severity).toLowerCase().includes('high')
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    Severidad: {r.severity || 'Medium'}
                  </span>
                </div>
                <p className="text-xs font-semibold text-[var(--text-primary)]">{r.description}</p>
                <div className="flex items-center gap-4 text-[11px] text-[var(--text-muted)]">
                  <span>CWE: {r.cwe || 'N/A'}</span>
                  <span>Confidencialidad: {r.confidentiality || 'N/A'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
