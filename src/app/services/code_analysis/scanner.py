"""
@file scanner.py
@author naflashDev
@brief Lógica de escaneo de código fuente para vulnerabilidades.
@details Implementa el análisis usando bandit y LLM CyberSentinel, y la generación de reportes PDF.
"""

from loguru import logger
from typing import List, Dict, Any
import subprocess
import tempfile
import base64
from fpdf import FPDF
from datetime import datetime
from typing import Callable

# Importación condicional del LLM solo si está activado en los .ini
import app.services.llm.llm_client as llm_client
from app.utils.utils import read_file
import os

def is_llm_enabled_src():
    '''
    @brief Comprueba si el flag use_ollama está activado en algún .ini de src/.
    @return True si está activado, False si no.
    '''
    # Build a list of candidate paths where configuration file may live.
    # scanner.py is located at: src/app/services/code_analysis/scanner.py
    # parents: [0]=code_analysis, [1]=services, [2]=app, [3]=src, [4]=project_root
    current = os.path.abspath(__file__)
    p = os.path.dirname(current)
    parents = []
    # collect up to 5 levels to be safe
    for _ in range(5):
        parents.append(p)
        p = os.path.dirname(p)

    candidates = []
    # try src/app (parents[2]) and src (parents[3]) and project root (parents[4])
    try:
        app_dir = parents[2]
        src_dir = parents[3]
        root_dir = parents[4]
    except Exception:
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        src_dir = os.path.dirname(app_dir)
        root_dir = os.path.dirname(src_dir)

    # Prefer project root configs first (allows tests/CI to override repo defaults),
    # then src/, then app/. We treat each directory as a precedence group: if any
    # file exists in that directory, we only consult files from that directory and
    # return the first explicit `use_ollama` value found (True/False). If none of
    # the existing files in the group contain the flag, we consider it disabled
    # for that group (do NOT fall back to lower-precedence directories).
    root_cfg = os.path.join(root_dir, 'cfg.ini')
    root_serv = os.path.join(root_dir, 'cfg_services.ini')
    src_cfg = os.path.join(src_dir, 'cfg.ini')
    src_serv = os.path.join(src_dir, 'cfg_services.ini')
    app_cfg = os.path.join(app_dir, 'cfg.ini')
    app_serv = os.path.join(app_dir, 'cfg_services.ini')

    precedence_groups = [
        [root_cfg, root_serv],
        [src_cfg, src_serv],
        [app_cfg, app_serv],
    ]

    logger = __import__('loguru').logger

    true_values = ('true', '1', 'yes', 'on')
    false_values = ('false', '0', 'no', 'off')

    # Walk groups in precedence order. If any file exists in the group, consult
    # only the files in that group and return the first explicit `use_ollama`
    # value found. If none of the existing files in the group contain the flag,
    # we treat the flag as disabled for that group (do NOT fall back).
    for group in precedence_groups:
        existing_files = [f for f in group if os.path.exists(f)]
        if not existing_files:
            continue

        # Inspect files in this group for the flag
        for ini_file in existing_files:
            ret = read_file(ini_file, ['#', '\n'])
            if isinstance(ret, tuple) and len(ret) == 3:
                lines = ret[2]
                for line in lines:
                    if 'use_ollama' in line.lower():
                        for part in line.split(';'):
                            if 'use_ollama' in part.lower():
                                try:
                                    k, v = part.split('=', 1)
                                except Exception:
                                    continue
                                k = k.strip().lower()
                                v = v.strip().lower()
                                if k == 'use_ollama' and v in true_values:
                                    return True
                                if k == 'use_ollama' and v in false_values:
                                    return False

        # If we had files in this group but no explicit flag was found, consider
        # the flag disabled for this group and do not fall back to lower
        # precedence groups.
        # No explicit flag found in this precedence group -> treat as disabled for this group
        return False

    # No config files found at all, default to False
    # No config files found at all, default to False
    return False


class CodeScanner:
    '''
    @brief Clase para escanear código fuente y generar reportes.

    Permite analizar código usando Bandit (Python), Semgrep (multi-lenguaje), Flawfinder (C/C++), Gosec (Go) y un LLM para explicación de vulnerabilidades.
    '''

    def is_llm_enabled(self) -> bool:
        '''
        @brief Devuelve si el LLM está activado según la configuración.
        @return True si está activado, False si no.
        '''
        return is_llm_enabled_src()

    def __init__(self, llm=None):
        '''
        @brief Optional LLM provider injection for easier testing.
        @param llm Either a callable or an object with `explain_vulnerability(text)`.
        '''
        self.llm = llm

    def _explain_with_llm(self, text: str) -> str:
        '''
        @brief Normalize calls to LLM. Prefer injected `self.llm` if present,
        otherwise call the runtime `llm_client.query_llm` so tests can monkeypatch it.
        '''
        try:
            # Honor injected provider for tests
            if hasattr(self, 'llm') and self.llm:
                provider = self.llm
                if hasattr(provider, 'explain_vulnerability') and callable(getattr(provider, 'explain_vulnerability')):
                    return provider.explain_vulnerability(text)
                if callable(provider):
                    return provider(text)

            # Base system prompt (Spanish, professional tone)
            base_system = (
                "Eres un asistente experto en ciberseguridad. Responde siempre en español, "
                "de forma clara, concisa y profesional. Al explicar vulnerabilidades, ofrece "
                "pasos accionables y utiliza terminología técnica apropiada para desarrolladores."
            )

            # Best-effort: attempt retrieval from local Chroma using Ollama embedder
            retrieved_block = ""
            try:
                from app.services.vectorstore.chroma_client import ChromaClient
                from app.services.vectorstore.ollama_adapter import OllamaEmbeddingAdapter

                try:
                    embedder = OllamaEmbeddingAdapter()
                    chroma = ChromaClient(embed_model=embedder)
                    docs = chroma.query_retriever(query=text, k=5) or []
                except Exception as e:
                    docs = []
                    logger.debug("RAG init failed or disabled: %s", e)

                if docs:
                    parts = []
                    for idx, d in enumerate(docs):
                        src = (d.get('metadata', {}) or {}).get('source') or d.get('id') or f'doc_{idx}'
                        snippet = (d.get('text') or "")[:800].replace("\n", " ")
                        parts.append(f"[{src}] {snippet}")
                    retrieved_block = "\n\n--- Retrieved documents ---\n" + "\n\n".join(parts) + "\n\n--- End retrieved ---\n"
            except Exception as e:
                logger.debug("Chroma import or query failed (RAG unavailable): %s", e)
                retrieved_block = ""

            # Compose final system prompt including retrieved context if any
            system_prompt = base_system
            if retrieved_block:
                system_prompt = base_system + "\n\nUtiliza la siguiente información recuperada de los documentos del usuario como contexto adicional. Si la información no es relevante para la pregunta, ignórala." + retrieved_block

            # Call the LLM client via chat-style messages when possible
            if hasattr(llm_client, 'query_llm') and callable(llm_client.query_llm):
                messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": text}]
                try:
                    return llm_client.query_llm(messages=messages)
                except TypeError:
                    # backward-compatible signature that accepts prompt + system_prompt
                    return llm_client.query_llm(text, system_prompt=system_prompt)
                except Exception as e:
                    logger.error("LLM query failed: %s", e)

        except Exception as e:
            logger.error(f"Error in _explain_with_llm: {e}")

        return 'LLM unavailable.'

    def _classify_confidentiality(self, text: str) -> str:
        '''
        @brief Heurística simple para estimar el impacto sobre la confidencialidad.
        @param text Texto (descripción, detalles) de la vulnerabilidad.
        @return Una de: 'High', 'Medium', 'Low', 'Unknown'
        '''
        if not text:
            return 'Unknown'

    def _severity_rank(self, sev: Any) -> int:
        '''
        @brief Convert a severity label into a sortable rank (higher = more severe).

        Accepts common textual severities (critical/high/medium/low/info) or numeric values.
        @param sev Severity label or numeric value.
        @return Integer rank where larger means more severe.
        '''
        if sev is None:
            return 0
        s = str(sev).strip().lower()
        if not s:
            return 0
        # textual mapping
        if any(x in s for x in ('critical', 'crit', 'cve-critical')):
            return 5
        if 'high' in s or s == 'h':
            return 4
        if 'medium' in s or s == 'm' or 'med' in s:
            return 3
        if 'low' in s or s == 'l':
            return 2
        if any(x in s for x in ('info', 'informational', 'notice')):
            return 1
        # try numeric
        try:
            n = float(''.join(ch for ch in s if (ch.isdigit() or ch == '.')) or 0)
            # map 0..10 scale into 0..5
            return min(5, max(0, int(round(n / 2))))
        except Exception:
            return 0

    def _group_and_sort_vulnerabilities(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        '''
        @brief Group identical vulnerabilities and sort groups by importance.

        Identical is defined by the combination of `cwe`, `description` and normalized severity.
        Groups keep a list of occurrences (filename + line) but include a single explanation.

        @param vulnerabilities List of vulnerability dicts as produced by scanners.
        @return List of grouped vulnerability dicts sorted by severity (desc) and occurrence count (desc).
        '''
        groups: Dict[Tuple[str, str, int], Dict[str, Any]] = {}

        for v in vulnerabilities:
            sev = v.get('severity')
            rank = self._severity_rank(sev)
            cwe = str(v.get('cwe') or '-').strip()
            desc = str(v.get('description') or '').strip()
            # key: severity rank + cwe + description
            key = (cwe, desc, rank)

            occ = {
                'filename': v.get('filename', '-'),
                'line': v.get('line', '-')
            }

            if key not in groups:
                groups[key] = {
                    'severity': sev or '-',
                    'severity_rank': rank,
                    'cwe': cwe,
                    'description': desc or '-',
                    'explanation': str(v.get('explanation') or '-'),
                    'occurrences': [occ],
                    'count': 1,
                }
            else:
                groups[key]['occurrences'].append(occ)
                groups[key]['count'] += 1

        # Convert to list and sort: primary by severity_rank desc, then by count desc
        grouped_list = list(groups.values())
        grouped_list.sort(key=lambda g: (g['severity_rank'], g['count']), reverse=True)
        return grouped_list
        t = text.lower()
        high_keywords = ('expos', 'leak', 'information disclosure', 'sensitive', 'secret', 'credentials', 'password', 'token', 'key', 'ssn', 'pii', 'personal data')
        medium_keywords = ('access control', 'authorization', 'auth bypass', 'insecure direct object', 'idor', 'privacy')
        for kw in high_keywords:
            if kw in t:
                return 'High'
        for kw in medium_keywords:
            if kw in t:
                return 'Medium'
        # If the description mentions data or files, consider Medium
        if 'data' in t or 'file' in t or 'database' in t:
            return 'Medium'
        return 'Low'

    # NOTE: single constructor above accepts optional `llm` injection for tests.

    def detect_language(self, code: str) -> str:
        '''
        @brief Detecta el lenguaje del código fuente recibido.
        @param code Código fuente como string.
        @return Nombre del lenguaje detectado ("python", "go", "c", "cpp", "javascript", "java", etc.)
        '''
        # Heurística simple por palabras clave
        code_lc = code.lower()
        if any(kw in code_lc for kw in ("def ", "import ", "class ", "self", "print(", "except", "lambda ", "elif ", "eval(")):
            return "python"
        if any(kw in code_lc for kw in ("package main", "func ", "import ", "fmt.", "go ", "defer ", "chan ")):
            return "go"
        if any(kw in code_lc for kw in ("#include", "int main", "printf(", "scanf(", "malloc", "free", "void ")):
            return "c"
        if any(kw in code_lc for kw in ("#include", "std::", "cout", "cin", "new ", "delete ", "class ", "public:", "private:")):
            return "cpp"
        if any(kw in code_lc for kw in ("function ", "const ", "let ", "var ", "=>", "console.log", "require(", "module.exports")):
            return "javascript"
        if any(kw in code_lc for kw in ("public static void main", "System.out.println", "class ", "import java.", "package ")):
            return "java"
        return "unknown"

    def scan_text(self, code: str, source_filename: str | None = None) -> List[Dict[str, Any]]:
        '''
        @brief Analiza el código recibido y detecta vulnerabilidades usando la herramienta adecuada.

        @param code Código fuente como string.
        @return Lista de vulnerabilidades encontradas.
        '''
        import json
        import re
        try:
            lang = self.detect_language(code)
            logger.info(f"Lenguaje detectado: {lang}")
            # Guardar código en archivo temporal con extensión adecuada
            ext = {
                "python": ".py",
                "go": ".go",
                "c": ".c",
                "cpp": ".cpp",
                "javascript": ".js",
                "java": ".java"
            }.get(lang, ".txt")
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=ext) as tmp:
                tmp.write(code)
                tmp_path = tmp.name
            # Determine a sensible filename to attribute vulnerabilities to.
            # Prefer an explicit source_filename passed by the caller (e.g. upload),
            # otherwise use the temporary file's basename.
            attributed_filename = source_filename if source_filename else os.path.basename(tmp_path)
            logger.debug(f"[scanner] Archivo temporal creado para análisis: {tmp_path}")
            logger.debug(f"[scanner] Primeros 200 caracteres escritos: {repr(code)[:200]}")

            llm_enabled = is_llm_enabled_src()
            logger.info(f"LLM activado según .ini en src/: {llm_enabled}")

            if lang == "python":
                # Bandit
                try:
                    result = subprocess.run(["bandit", "-f", "json", "-r", tmp_path], capture_output=True, text=True)
                except Exception as e:
                    logger.error(f"Bandit invocation error: {e}")
                    return []
                logger.debug(f"Bandit stdout: {result.stdout}")
                logger.debug(f"Bandit stderr: {result.stderr}")
                bandit_output = (result.stdout or "").strip()
                try:
                    data = json.loads(bandit_output) if bandit_output else {"results": []}
                except Exception:
                    logger.error(f"Salida de Bandit no es JSON válido: {bandit_output}")
                    return []
                # Manejo explícito de errores de sintaxis
                if data.get("errors"):
                    reasons = ", ".join([e.get("reason", "") for e in data["errors"]])
                    logger.error(f"Bandit reportó error de sintaxis: {reasons}")
                    return []
                vulns = []
                for issue in data.get("results", []):
                    if llm_enabled:
                        explanation = self._explain_with_llm(issue.get("issue_text", ""))
                    else:
                        explanation = "LLM desactivado por configuración."
                    desc = issue.get("issue_text") or issue.get("message") or "-"
                    confidentiality = self._classify_confidentiality(desc)
                    vulns.append({
                        "line": issue.get("line_number") or issue.get("line") or (issue.get("start") or {}).get("line"),
                        "severity": issue.get("issue_severity") or issue.get("severity") or "-",
                        "description": desc,
                        "cwe": (issue.get("cwe") or {}).get("id") or issue.get("check_id") or "N/A",
                        "explanation": explanation,
                        "filename": attributed_filename,
                        "confidentiality": confidentiality,
                    })
                return vulns
            elif lang == "go":
                # Gosec
                result = subprocess.run(["gosec", "-fmt=json", tmp_path], capture_output=True, text=True)
                logger.debug(f"Gosec stdout: {result.stdout}")
                logger.debug(f"Gosec stderr: {result.stderr}")
                gosec_output = result.stdout.strip()
                if not gosec_output or not (gosec_output.startswith('{') and gosec_output.endswith('}')):
                    logger.error(f"Salida de Gosec no es JSON válido: {gosec_output}")
                    raise ValueError("La salida de Gosec no es JSON válido. ¿Es código Go?")
                data = json.loads(gosec_output)
                vulns = []
                for issue in data.get("Issues", []):
                    if llm_enabled:
                        explanation = self._explain_with_llm(issue.get("details", ""))
                    else:
                        explanation = "LLM desactivado por configuración."
                    desc = issue.get("details", "-")
                    confidentiality = self._classify_confidentiality(desc)
                    vulns.append({
                        "line": issue.get("line", "-"),
                        "severity": issue.get("severity", "-"),
                        "description": desc,
                        "cwe": issue.get("cwe", {}).get("ID", "N/A"),
                        "explanation": explanation,
                        "filename": attributed_filename,
                        "confidentiality": confidentiality,
                    })
                return vulns
            elif lang == "c" or lang == "cpp":
                # Flawfinder
                result = subprocess.run(["flawfinder", "--quiet", "--dataonly", tmp_path], capture_output=True, text=True)
                logger.debug(f"Flawfinder stdout: {result.stdout}")
                logger.debug(f"Flawfinder stderr: {result.stderr}")
                flaw_output = result.stdout.strip()
                # Flawfinder output is not JSON, parse lines
                vulns = []
                for line in flaw_output.splitlines():
                    # CSV: filename:linenumber|level|category|message
                    parts = line.split("|")
                    if len(parts) >= 4:
                        file_line, level, category, message = parts[:4]
                        try:
                            lineno = int(file_line.split(":")[-1])
                        except Exception:
                            lineno = "-"
                        if llm_enabled:
                            explanation = self._explain_with_llm(message)
                        else:
                            explanation = "LLM desactivado por configuración."
                        desc = message
                        confidentiality = self._classify_confidentiality(desc)
                        vulns.append({
                            "line": lineno,
                            "severity": level,
                            "description": desc,
                            "cwe": category,
                            "explanation": explanation,
                            "filename": attributed_filename,
                            "confidentiality": confidentiality,
                        })
                return vulns
            else:
                # Semgrep (multi-lenguaje, fallback)
                # Ensure semgrep runs with UTF-8 enabled on Windows to avoid
                # UnicodeEncodeError when semgrep writes/parses config files.
                semgrep_env = os.environ.copy()
                semgrep_env.setdefault('PYTHONUTF8', '1')
                semgrep_env.setdefault('PYTHONIOENCODING', 'utf-8')
                try:
                    try:
                        result = subprocess.run(["semgrep", "--json", tmp_path], capture_output=True, text=True, env=semgrep_env, encoding='utf-8', errors='replace')
                    except TypeError:
                        result = subprocess.run(["semgrep", "--json", tmp_path], capture_output=True, text=True, env=semgrep_env)
                except Exception as e:
                    logger.error(f"Semgrep invocation error: {e}")
                    return []
                logger.debug(f"Semgrep stdout: {result.stdout}")
                logger.debug(f"Semgrep stderr: {result.stderr}")
                semgrep_output = (result.stdout or "").strip()
                try:
                    data = json.loads(semgrep_output) if semgrep_output else {"results": []}
                except Exception:
                    logger.error(f"Salida de Semgrep no es JSON válido: {semgrep_output}")
                    return []
                vulns = []
                for res in data.get("results", []):
                    line = res.get('line_number') or (res.get('start') or {}).get('line') or '-'
                    severity = res.get('issue_severity') or res.get('severity') or (res.get('extra') or {}).get('severity') or '-'
                    description = res.get('issue_text') or res.get('message') or (res.get('extra') or {}).get('message') or '-'
                    cwe = (res.get('cwe') or {}).get('id') or res.get('check_id') or 'N/A'
                    if llm_enabled:
                        explanation = self._explain_with_llm(description)
                    else:
                        explanation = "LLM desactivado por configuración."
                    confidentiality = self._classify_confidentiality(description)
                    vulns.append({
                        'line': line,
                        'severity': severity,
                        'description': description,
                        'cwe': cwe,
                        'explanation': explanation,
                        'filename': attributed_filename,
                        'confidentiality': confidentiality,
                    })
                return vulns
        except Exception as e:
            logger.error(f"Error en scan_text: {e}")
            raise

    def scan_uploaded_file(self, file_bytes: bytes, filename: str | None = None) -> Dict[str, Any]:
        '''
        @brief Procesa un archivo subido (zip o fichero simple), escanea su contenido y genera el payload listo para la UI.

        @param file_bytes Contenido del archivo subido en bytes.
        @param filename Nombre original del archivo subido (puede ser None).
        @return Diccionario con claves: `vulnerabilities`, `vulnerabilities_full`, `llm_enabled`, `pdf_base64`.
        '''
        import zipfile, tempfile, os, shutil

        results: List[Dict[str, Any]] = []
        pdf_b64 = None
        llm_enabled = self.is_llm_enabled() if hasattr(self, 'is_llm_enabled') else False

        # Manejo ZIP
        if filename and filename.lower().endswith('.zip'):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
                    tmp_zip.write(file_bytes)
                    tmp_zip_path = tmp_zip.name
                with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
                    extract_dir = tempfile.mkdtemp()
                    zip_ref.extractall(extract_dir)
                    # Recorrer archivos extraídos y analizar los de código soportados
                    extensiones = ('.py', '.js', '.java', '.c', '.cpp', '.rb', '.go')
                    for root, _, files in os.walk(extract_dir):
                        for fname in files:
                            if fname.endswith(extensiones):
                                fpath = os.path.join(root, fname)
                                try:
                                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                    # Pass the extracted file's name so scanner attributes findings correctly
                                    res = self.scan_text(content, source_filename=fname)
                                    results.extend(res)
                                except Exception as e:
                                    logger.error(f"[scanner.scan_uploaded_file] Error analizando {fname}: {e}")
                pdf_b64 = self.generate_pdf_report(results) if results else None
            finally:
                try:
                    if 'tmp_zip_path' in locals() and os.path.exists(tmp_zip_path):
                        os.remove(tmp_zip_path)
                except Exception:
                    pass
                try:
                    if 'extract_dir' in locals() and os.path.exists(extract_dir):
                        shutil.rmtree(extract_dir)
                except Exception:
                    pass
            ui_results = [{k: v for k, v in r.items() if k != 'explanation'} for r in results]
            return {"vulnerabilities": ui_results, "vulnerabilities_full": results, "llm_enabled": llm_enabled, "pdf_base64": pdf_b64}

        # Fichero único (no zip)
        try:
            try:
                content = file_bytes.decode('utf-8', errors='ignore')
            except Exception:
                content = ''
            results = self.scan_text(content, source_filename=filename)
            pdf_b64 = self.generate_pdf_report(results) if results else None
            ui_results = [{k: v for k, v in r.items() if k != 'explanation'} for r in results]
            return {"vulnerabilities": ui_results, "vulnerabilities_full": results, "llm_enabled": llm_enabled, "pdf_base64": pdf_b64}
        except Exception as e:
            logger.error(f"[scanner.scan_uploaded_file] Error procesando archivo subido: {e}")
            raise

    def generate_pdf_report(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        '''
        @brief Genera un informe PDF a partir de los resultados del análisis.

        Usa fpdf2 para crear un PDF y lo devuelve codificado en base64.

        @param vulnerabilities Lista de vulnerabilidades encontradas.
        @return PDF codificado en base64.
        '''
        from fpdf.errors import FPDFException

        class PDF(FPDF):
            def header(self):
                # Title
                self.set_font("Arial", 'B', 14)
                self.set_text_color(33, 37, 41)
                self.cell(0, 8, "Informe de Análisis de Código", ln=True, align="C")
                self.ln(2)

            def footer(self):
                # Page number + small footer
                self.set_y(-12)
                self.set_font("Arial", 'I', 8)
                self.set_text_color(100)
                self.cell(0, 8, f"CyberMind - Página {self.page_no()}", align="C")

        pdf = PDF()
        pdf.set_auto_page_break(True, margin=15)
        pdf.add_page()

        # Header info
        pdf.set_font("Arial", size=10)
        generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        pdf.cell(0, 6, f"Fecha de generación: {generated_at}", ln=True)
        pdf.cell(0, 6, f"Vulnerabilidades totales: {len(vulnerabilities)}", ln=True)
        pdf.ln(4)

        # Summary by severity
        counts: Dict[str, int] = {}
        for v in vulnerabilities:
            key = str(v.get('severity') or '-')
            counts[key] = counts.get(key, 0) + 1
        summary_parts = [f"{k}: {counts[k]}" for k in counts]
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, "Resumen por severidad:", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, " | ".join(summary_parts) or "-")
        pdf.ln(6)

        # Summary by confidentiality
        conf_counts: Dict[str, int] = {}
        for v in vulnerabilities:
            ck = str(v.get('confidentiality') or 'Unknown')
            conf_counts[ck] = conf_counts.get(ck, 0) + 1
        conf_parts = [f"{k}: {conf_counts[k]}" for k in conf_counts]
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, "Resumen por confidencialidad:", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, " | ".join(conf_parts) or "-")
        pdf.ln(6)

        # Detailed entries: group identical vulnerabilities and show explanation once per group
        grouped = self._group_and_sort_vulnerabilities(vulnerabilities)
        if not grouped:
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 6, "No hay vulnerabilidades detalladas.", ln=True)
        else:
            for idx, g in enumerate(grouped, start=1):
                severity = g.get('severity', '-')
                cwe = g.get('cwe', '-')
                description = g.get('description', '-')
                explanation = g.get('explanation', '-')
                occs = g.get('occurrences', [])
                count = g.get('count', len(occs))

                # Header for the grouped vulnerability
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(0, 6, f"{idx}. Severidad: {severity} - CWE: {cwe} - Ocurrencias: {count}", ln=True)
                pdf.set_font("Arial", size=10)
                try:
                    pdf.multi_cell(0, 6, f"Descripción: {description}")
                except FPDFException:
                    pdf.multi_cell(0, 6, f"Descripción: {description[:200]}")
                pdf.ln(1)

                # List occurrences (file:line), but keep it compact
                try:
                    occ_lines = [f"{o.get('filename','-')}:{o.get('line','-')}" for o in occs]
                    pdf.multi_cell(0, 6, "Ubicaciones: " + (", ".join(occ_lines) or "-"))
                except FPDFException:
                    pdf.multi_cell(0, 6, "Ubicaciones: -")
                pdf.ln(1)

                # Single explanation per grouped vulnerability
                pdf.set_font("Arial", 'I', 10)
                try:
                    pdf.multi_cell(0, 6, f"Explicación LLM: {explanation}")
                except FPDFException:
                    pdf.multi_cell(0, 6, f"Explicación LLM: {explanation[:300]}")
                pdf.ln(4)

        # Write to temporary file and return base64
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            tmp_pdf_path = tmp_pdf.name

        try:
            with open(tmp_pdf_path, "rb") as f:
                pdf_bytes = f.read()
        finally:
            try:
                os.remove(tmp_pdf_path)
            except Exception:
                pass

        return base64.b64encode(pdf_bytes).decode("utf-8")
