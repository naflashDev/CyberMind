"""
@file test_scanner_llm_flag.py
@author naflashDev
@brief Tests unitarios para el uso condicional del LLM en CodeScanner.
@details Cubre casos donde el flag use_ollama está activado o desactivado en los .ini de src/.
"""
import os
import pytest
from src.app.services.code_analysis.scanner import CodeScanner, is_llm_enabled_src

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INI_CFG = os.path.join(SRC_DIR, 'cfg.ini')
INI_SERV = os.path.join(SRC_DIR, 'cfg_services.ini')

@pytest.fixture(autouse=True)
def cleanup_ini():
    # Limpia los .ini tras cada test
    yield
    for f in [INI_CFG, INI_SERV]:
        if os.path.exists(f):
            os.remove(f)

@pytest.mark.parametrize("ini_content,expected", [
    ("use_ollama=true", True),
    ("use_ollama=false", False),
    ("# sin flag", False),
    ("distro_name=Ubuntu;use_ollama=true", True),
    ("distro_name=Ubuntu;use_ollama=false", False),
])
def test_is_llm_enabled_src(ini_content, expected):
    with open(INI_CFG, 'w') as f:
        f.write(ini_content)
    assert is_llm_enabled_src() == expected


def test_scan_text_llm(monkeypatch):
    # Si el flag está en true, debe llamar a query_llm
    with open(INI_CFG, 'w') as f:
        f.write('use_ollama=true')
    called = {}
    def fake_query_llm(txt):
        called['ok'] = True
        return 'LLM OK'
    monkeypatch.setattr('src.app.services.llm.llm_client.query_llm', fake_query_llm)
    scanner = CodeScanner()
    # Simula salida de Bandit
    def fake_bandit(*a, **kw):
        class R: stdout = '{"results":[{"issue_text":"prob","line_number":1,"issue_severity":"HIGH","cwe":{"id":"CWE-1"}}]}'; stderr = ''
        return R()
    monkeypatch.setattr('subprocess.run', fake_bandit)
    vulns = scanner.scan_text('def f(): pass')
    assert called.get('ok')
    assert vulns[0]['explanation'] == 'LLM OK'

def test_scan_text_no_llm(monkeypatch):
    # Si el flag está en false, no debe llamar a query_llm
    with open(INI_CFG, 'w') as f:
        f.write('use_ollama=false')
    called = {}
    def fake_query_llm(txt):
        called['fail'] = True
        return 'NO'
    monkeypatch.setattr('src.app.services.llm.llm_client.query_llm', fake_query_llm)
    scanner = CodeScanner()
    def fake_bandit(*a, **kw):
        class R: stdout = '{"results":[{"issue_text":"prob","line_number":1,"issue_severity":"HIGH","cwe":{"id":"CWE-1"}}]}'; stderr = ''
        return R()
    monkeypatch.setattr('subprocess.run', fake_bandit)
    vulns = scanner.scan_text('def f(): pass')
    assert not called
    assert vulns[0]['explanation'] == 'LLM desactivado por configuración.'
