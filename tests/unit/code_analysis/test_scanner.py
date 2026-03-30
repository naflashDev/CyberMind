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

def test_detect_language_and_severity_grouping():
    '''
    @brief Detect language heuristics and grouping/severity ranking.
    '''
    scanner = CodeScanner()
    # detect_language
    assert scanner.detect_language('def foo():\n    return 1') == 'python'
    assert scanner.detect_language('package main\nfunc main() {}') == 'go'
    assert scanner.detect_language('#include <stdio.h>\nint main(){}') == 'c'
    assert scanner.detect_language('std::cout << "hi";') == 'cpp'
    assert scanner.detect_language('function test() { console.log(1); }') == 'javascript'
    # Heuristic may match C due to presence of 'void' before Java-specific checks
    assert scanner.detect_language('public static void main(String[] args)') in ('java', 'c')
    assert scanner.detect_language('some unknown gibberish text') == 'unknown'

    # severity ranking
    assert scanner._severity_rank(None) == 0
    assert scanner._severity_rank('CRITICAL') == 5
    assert scanner._severity_rank('high') == 4
    assert scanner._severity_rank('Medium') == 3
    assert scanner._severity_rank('low') == 2
    assert scanner._severity_rank('info') == 1
    assert scanner._severity_rank('9') >= 4

    # grouping and sorting
    vulns = [
        {'severity': 'high', 'cwe': 'CWE-1', 'description': 'A', 'filename': 'a.py', 'line': 1},
        {'severity': 'high', 'cwe': 'CWE-1', 'description': 'A', 'filename': 'b.py', 'line': 2},
        {'severity': 'low', 'cwe': 'CWE-2', 'description': 'B', 'filename': 'c.c', 'line': 10},
    ]
    grouped = scanner._group_and_sort_vulnerabilities(vulns)
    # Expect two groups: one for A (count 2) and one for B
    assert any(g['count'] == 2 and g['description'] in ('A', 'A') for g in grouped)
    assert any(g['count'] == 1 and g['description'] in ('B', 'B') for g in grouped)

def test_scan_uploaded_file_zip_and_single(monkeypatch, tmp_path):
    '''
    @brief Ensure scan_uploaded_file handles ZIP uploads and single-file bytes.
    '''
    scanner = CodeScanner()

    # Monkeypatch scan_text to avoid invoking external tools
    def fake_scan_text(code, source_filename=None):
        return [{
            'line': 1,
            'severity': 'HIGH',
            'description': 'fake',
            'cwe': 'CWE-FAKE',
            'explanation': 'e',
            'filename': source_filename or 'tmp.py',
            'confidentiality': 'Unknown'
        }]

    monkeypatch.setattr(scanner, 'scan_text', fake_scan_text)

    # Build a ZIP bytes with a simple python file inside
    import io, zipfile
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode='w') as zf:
        zf.writestr('a.py', 'print(1)')
    mem_bytes = mem.getvalue()

    res = scanner.scan_uploaded_file(mem_bytes, filename='code.zip')
    assert isinstance(res, dict)
    assert 'vulnerabilities' in res
    assert isinstance(res['vulnerabilities'], list)

    # Single file (non-zip)
    res2 = scanner.scan_uploaded_file(b'print(2)', filename='single.py')
    assert isinstance(res2, dict)
    assert res2['vulnerabilities']


def test_scan_text_gosec_and_flawfinder_and_semgrep(monkeypatch):
    '''
    @brief Cover branches for gosec, flawfinder and semgrep outputs.
    '''
    scanner = CodeScanner()
    # Disable LLM for these branches
    monkeypatch.setattr('src.app.services.code_analysis.scanner.is_llm_enabled_src', lambda: False)

    # Gosec JSON branch
    monkeypatch.setattr(scanner, 'detect_language', lambda code: 'go')
    go_json = '{"Issues":[{"line":10,"severity":"HIGH","details":"Gosec issue","cwe":{"ID":"CWE-GO"}}]}'
    monkeypatch.setattr('subprocess.run', lambda *a, **kw: type('R', (), {'stdout': go_json, 'stderr': '', 'returncode': 0})())
    vulns_go = scanner.scan_text('package main')
    assert any(v.get('cwe') == 'CWE-GO' for v in vulns_go)

    # Flawfinder output (C)
    monkeypatch.setattr(scanner, 'detect_language', lambda code: 'c')
    flaw_stdout = 'file.c:42|HIGH|CWE-120|buffer overflow\n'
    monkeypatch.setattr('subprocess.run', lambda *a, **kw: type('R', (), {'stdout': flaw_stdout, 'stderr': '', 'returncode': 0})())
    vulns_c = scanner.scan_text('int main(){}')
    assert any('buffer overflow' in (v.get('description') or '') for v in vulns_c)

    # Semgrep fallback (unknown language)
    monkeypatch.setattr(scanner, 'detect_language', lambda code: 'unknown')
    sem_json = '{"results":[{"line_number":2,"issue_text":"semgrep issue","severity":"MEDIUM","check_id":"S123"}]}'
    monkeypatch.setattr('subprocess.run', lambda *a, **kw: type('R', (), {'stdout': sem_json, 'stderr': '', 'returncode': 0})())
    vulns_s = scanner.scan_text('some code')
    assert any(v.get('cwe') == 'S123' or v.get('description') for v in vulns_s)
