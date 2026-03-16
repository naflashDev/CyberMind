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

# Importación condicional del LLM solo si está activado en los .ini
from app.services.llm.llm_client import query_llm
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
    # then src/, then app/.
    candidates.extend([
        os.path.join(root_dir, 'cfg.ini'),
        os.path.join(root_dir, 'cfg_services.ini'),
        os.path.join(src_dir, 'cfg.ini'),
        os.path.join(src_dir, 'cfg_services.ini'),
        os.path.join(app_dir, 'cfg.ini'),
        os.path.join(app_dir, 'cfg_services.ini'),
    ])

    logger = __import__('loguru').logger
    logger.debug(f"[is_llm_enabled_src] Candidate config paths: {candidates}")

    for ini_file in candidates:
        if os.path.exists(ini_file):
            ret = read_file(ini_file, ['#', '\n'])
            logger.debug(f"[is_llm_enabled_src] Resultado de read_file({ini_file}): {ret}")
            if isinstance(ret, tuple) and len(ret) == 3:
                lines = ret[2]
                logger.debug(f"[is_llm_enabled_src] Líneas leídas de {ini_file}: {lines}")
                for line in lines:
                    logger.debug(f"[is_llm_enabled_src] Analizando línea: {line}")
                    if 'use_ollama' in line.lower():
                        for part in line.split(';'):
                            if 'use_ollama' in part.lower():
                                try:
                                    k, v = part.split('=', 1)
                                except Exception:
                                    continue
                                k = k.strip().lower()
                                v = v.strip().lower()
                                logger.debug(f"[is_llm_enabled_src] Encontrado: {k} = {v}")
                                if k == 'use_ollama' and v in ('true', '1', 'yes', 'on'):
                                    logger.info("[is_llm_enabled_src] use_ollama=true detectado, devolviendo True")
                                    return True
    logger.info("[is_llm_enabled_src] use_ollama=true NO detectado, devolviendo False")
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

    def detect_language(self, code: str) -> str:
        '''
        @brief Detecta el lenguaje del código fuente recibido.
        @param code Código fuente como string.
        @return Nombre del lenguaje detectado ("python", "go", "c", "cpp", "javascript", "java", etc.)
        '''
        # Heurística simple por palabras clave
        code_lc = code.lower()
        if any(kw in code_lc for kw in ("def ", "import ", "class ", "self", "print(", "except", "lambda ", "elif ")):
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

    def scan_text(self, code: str) -> List[Dict[str, Any]]:
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
            logger.debug(f"[scanner] Archivo temporal creado para análisis: {tmp_path}")
            logger.debug(f"[scanner] Primeros 200 caracteres escritos: {repr(code)[:200]}")

            llm_enabled = is_llm_enabled_src()
            logger.info(f"LLM activado según .ini en src/: {llm_enabled}")

            if lang == "python":
                # Bandit
                result = subprocess.run(["bandit", "-f", "json", "-r", tmp_path], capture_output=True, text=True)
                logger.debug(f"Bandit stdout: {result.stdout}")
                logger.debug(f"Bandit stderr: {result.stderr}")
                bandit_output = result.stdout.strip()
                if not bandit_output or not (bandit_output.startswith('{') and bandit_output.endswith('}')):
                    logger.error(f"Salida de Bandit no es JSON válido: {bandit_output}")
                    raise ValueError("La salida de Bandit no es JSON válido. ¿Es código Python?")
                data = json.loads(bandit_output)
                # Manejo explícito de errores de sintaxis
                if data.get("errors"):
                    reasons = ", ".join([e.get("reason", "") for e in data["errors"]])
                    logger.error(f"Bandit reportó error de sintaxis: {reasons}")
                    raise ValueError(f"Bandit reportó error de sintaxis: {reasons}")
                vulns = []
                for issue in data.get("results", []):
                    if llm_enabled:
                        explanation = query_llm(issue.get("issue_text", ""))
                    else:
                        explanation = "LLM desactivado por configuración."
                    vulns.append({
                        "line": issue.get("line_number"),
                        "severity": issue.get("issue_severity"),
                        "description": issue.get("issue_text"),
                        "cwe": issue.get("cwe", {}).get("id", "N/A"),
                        "explanation": explanation
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
                        explanation = query_llm(issue.get("details", ""))
                    else:
                        explanation = "LLM desactivado por configuración."
                    vulns.append({
                        "line": issue.get("line", "-"),
                        "severity": issue.get("severity", "-"),
                        "description": issue.get("details", "-"),
                        "cwe": issue.get("cwe", {}).get("ID", "N/A"),
                        "explanation": explanation
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
                            explanation = query_llm(message)
                        else:
                            explanation = "LLM desactivado por configuración."
                        vulns.append({
                            "line": lineno,
                            "severity": level,
                            "description": message,
                            "cwe": category,
                            "explanation": explanation
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
                    result = subprocess.run(["semgrep", "--json", tmp_path], capture_output=True, text=True, env=semgrep_env, encoding='utf-8', errors='replace')
                except TypeError:
                    # Older Python versions may not accept encoding/errors in subprocess.run
                    result = subprocess.run(["semgrep", "--json", tmp_path], capture_output=True, text=True, env=semgrep_env)
                logger.debug(f"Semgrep stdout: {result.stdout}")
                logger.debug(f"Semgrep stderr: {result.stderr}")
                semgrep_output = (result.stdout or "").strip()
                if not semgrep_output or not (semgrep_output.startswith('{') and semgrep_output.endswith('}')):
                    logger.error(f"Salida de Semgrep no es JSON válido: {semgrep_output}")
                    raise ValueError("La salida de Semgrep no es JSON válido.")
                data = json.loads(semgrep_output)
                vulns = []
                for result in data.get("results", []):
                    if llm_enabled:
                        explanation = query_llm(result.get("extra", {}).get("message", ""))
                    else:
                        explanation = "LLM desactivado por configuración."
                    vulns.append({
                        "line": result.get("start", {}).get("line", "-"),
                        "severity": result.get("extra", {}).get("severity", "-"),
                        "description": result.get("extra", {}).get("message", "-"),
                        "cwe": result.get("check_id", "N/A"),
                        "explanation": explanation
                    })
                return vulns
        except Exception as e:
            logger.error(f"Error en scan_text: {e}")
            raise

    def generate_pdf_report(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        '''
        @brief Genera un informe PDF a partir de los resultados del análisis.

        Usa fpdf2 para crear un PDF y lo devuelve codificado en base64.

        @param vulnerabilities Lista de vulnerabilidades encontradas.
        @return PDF codificado en base64.
        '''
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Informe de Análisis de Código", ln=True, align="C")
        pdf.ln(10)
        for v in vulnerabilities:
            pdf.set_font("Arial", style="B", size=11)
            pdf.cell(0, 8, txt=f"Línea: {v.get('line', '-')}", ln=True)
            pdf.set_font("Arial", size=11)
            pdf.cell(0, 8, txt=f"Severidad: {v.get('severity', '-')}", ln=True)
            pdf.multi_cell(0, 8, txt=f"Descripción: {v.get('description', '-')}")
            pdf.multi_cell(0, 8, txt=f"CWE: {v.get('cwe', '-')}")
            if v.get('explanation'):
                pdf.set_font("Arial", style="I", size=10)
                pdf.multi_cell(0, 8, txt=f"Explicación LLM: {v['explanation']}")
            pdf.ln(4)
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            tmp_pdf_path = tmp_pdf.name
        # Ahora abrir en modo lectura binaria
        with open(tmp_pdf_path, "rb") as f:
            pdf_bytes = f.read()
        return base64.b64encode(pdf_bytes).decode("utf-8")
