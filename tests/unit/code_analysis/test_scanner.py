"""
@file test_scanner.py
@author naflashDev
@brief Tests unitarios para CodeScanner (análisis de código).
@details Cubre casos Happy Path, Edge Case y Error Handling para el escaneo de código y generación de PDF.
"""
import pytest
from src.app.services.code_analysis.scanner import CodeScanner

class DummyLLM:
    def explain_vulnerability(self, text):
        return "Explicación simulada."

def test_scan_text_happy(monkeypatch):
    '''
    @brief Happy Path: código Python vulnerable.
    '''
    scanner = CodeScanner()
    # Monkeypatch LLM y bandit
    monkeypatch.setattr(scanner, 'llm', DummyLLM())
    # Ensure the scanner believes the LLM is enabled in config for this test
    monkeypatch.setattr('src.app.services.code_analysis.scanner.is_llm_enabled_src', lambda: True)
    monkeypatch.setattr('subprocess.run', lambda *a, **kw: type('R', (), {'returncode':0,'stdout':'{"results":[{"line_number":1,"issue_severity":"HIGH","issue_text":"Uso de eval() inseguro.","cwe":{"id":"CWE-95"}}]}','stderr':''})() )
    vulns = scanner.scan_text('eval("2+2")')
    assert len(vulns) == 1
    assert vulns[0]['severity'] == 'HIGH'
    assert vulns[0]['cwe'] == 'CWE-95'
    assert 'Explicación' in vulns[0]['explanation']

def test_scan_text_empty(monkeypatch):
    '''
    @brief Edge Case: código vacío.
    '''
    scanner = CodeScanner()
    monkeypatch.setattr(scanner, 'llm', DummyLLM())
    monkeypatch.setattr('subprocess.run', lambda *a, **kw: type('R', (), {'returncode':0,'stdout':'{"results":[]}','stderr':''})() )
    vulns = scanner.scan_text('')
    assert vulns == []

def test_scan_text_error(monkeypatch):
    '''
    @brief Error Handling: excepción en bandit.
    '''
    scanner = CodeScanner()
    monkeypatch.setattr(scanner, 'llm', DummyLLM())
    monkeypatch.setattr('subprocess.run', lambda *a, **kw: (_ for _ in ()).throw(Exception('bandit error')) )
    vulns = scanner.scan_text('print(1)')
    assert vulns == []

def test_generate_pdf_report():
    '''
    @brief Happy Path: generación de PDF con vulnerabilidades.
    '''
    scanner = CodeScanner()
    vulns = [{"line":1,"severity":"HIGH","description":"Test vuln.","cwe":"CWE-1","explanation":"Explicación."}]
    pdf_b64 = scanner.generate_pdf_report(vulns)
    assert isinstance(pdf_b64, str)
    assert len(pdf_b64) > 20
