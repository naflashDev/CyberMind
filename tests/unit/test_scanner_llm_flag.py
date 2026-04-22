"""
@file test_scanner_llm_flag.py
@author naflashDev
@brief Tests unitarios para el uso condicional del LLM en CodeScanner.
@details Cubre casos donde el flag use_ollama está activado o desactivado en los .ini de src/.
"""
import os
import time
import gc
import pytest
from src.app.services.code_analysis.scanner import CodeScanner, is_llm_enabled_src

SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INI_CFG = os.path.join(SRC_DIR, 'cfg.ini')
INI_SERV = os.path.join(SRC_DIR, 'cfg_services.ini')
CONV_DB = os.path.join(SRC_DIR, 'conversations.db')

@pytest.fixture(autouse=True)
def cleanup_ini():
    # Limpia los .ini tras cada test
    yield
    # On Windows a file may remain briefly locked by another process; retry
    for f in [INI_CFG, INI_SERV, CONV_DB]:
        if not os.path.exists(f):
            continue
        for _ in range(6):
            try:
                os.remove(f)
                break
            except PermissionError:
                # force GC and give the OS time to release handles
                gc.collect()
                time.sleep(0.1)
        else:
            # last attempt ignoring errors
            try:
                os.remove(f)
            except Exception:
                pass

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
    def fake_query_llm(*args, **kwargs):
        # Accept positional and keyword args to be compatible with callers
        called['ok'] = True
        return 'LLM OK'
    # Patch the runtime import used by scanner (app.services...), not the source path
    monkeypatch.setattr('app.services.llm.llm_client.query_llm', fake_query_llm)
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
    def fake_query_llm(*args, **kwargs):
        called['fail'] = True
        return 'NO'
    monkeypatch.setattr('app.services.llm.llm_client.query_llm', fake_query_llm)
    scanner = CodeScanner()
    def fake_bandit(*a, **kw):
        class R: stdout = '{"results":[{"issue_text":"prob","line_number":1,"issue_severity":"HIGH","cwe":{"id":"CWE-1"}}]}'; stderr = ''
        return R()
    monkeypatch.setattr('subprocess.run', fake_bandit)
    vulns = scanner.scan_text('def f(): pass')
    assert not called
    assert vulns[0]['explanation'] == 'LLM desactivado por configuración.'
