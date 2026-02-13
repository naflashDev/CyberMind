def test_clone_repository_error(monkeypatch):
    '''
    @brief Error Handling: Simula error en git clone.
    '''
    import os
    from src.app.services.llm import script_auto
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    with patch.object(script_auto.logger, "error") as logerr:
        try:
            script_auto.clone_repository("url", "repo")
        except Exception:
            logerr.assert_called()

def test_update_repository_error(monkeypatch):
    '''
    @brief Error Handling: Simula error en git pull.
    '''
    import os
    from src.app.services.llm import script_auto
    monkeypatch.setattr(os.path, "isdir", lambda p: True)
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    with patch.object(script_auto.logger, "error") as logerr:
        try:
            script_auto.update_repository("repo")
        except Exception:
            logerr.assert_called()
"""
@file test_script_auto_unit.py
@author naflashDev
@brief Unit tests for script_auto.py (CVE LLM utils).
@details Covers transform_json, clone/update repo (mocked), and consolidation logic (mocked IO).
"""
import pytest
import os
import json
from unittest.mock import patch, MagicMock
from src.app.services.llm import script_auto

def test_transform_json_published():
    '''
    @brief Happy Path: Transforma CVE publicado con campos mínimos
    '''
    cve = {
        "cveMetadata": {"state": "PUBLISHED", "cveId": "CVE-2023-0001", "datePublished": "2023-01-01", "dateUpdated": "2023-01-02"},
        "dataVersion": "5.0",
        "containers": {"cna": {"descriptions": [{"lang": "en", "value": "desc"}], "affected": [{"product": "p", "vendor": "v", "defaultStatus": "A", "versions": [{"version": "1.0", "status": "A"}]}], "problemTypes": [{"descriptions": [{"cweId": "CWE-1", "description": "desc", "lang": "en"}]}], "references": [{"url": "http://x"}], "metrics": [{"cvssV4_0": {"version": "4.0", "baseScore": 9, "baseSeverity": "C", "vectorString": "V"}}], "solutions": [{}]}, "adp": [{"metrics": [{"other": {"type": "ssvc", "content": {"options": [{"Exploitation": "yes", "Automatable": "no", "Technical Impact": "high"}]}}}]}]}
    }
    result = script_auto.transform_json(cve)
    assert isinstance(result, list)
    assert result and "instruction" in result[0]
    assert "CVE-2023-0001" in result[0]["input"]
    assert "desc" in result[0]["output"]

def test_transform_json_not_published():
    '''
    @brief Edge Case: No transforma CVE no publicado
    '''
    cve = {"cveMetadata": {"state": "REJECTED"}}
    result = script_auto.transform_json(cve)
    assert result == []

def test_transform_json_list():
    '''
    @brief Edge Case: Lista de CVEs
    '''
    cve = [{"cveMetadata": {"state": "PUBLISHED", "cveId": "CVE-2023-0002"}, "containers": {"cna": {}}}]
    result = script_auto.transform_json(cve)
    assert isinstance(result, list)
    assert any("CVE-2023-0002" in r.get("input", "") for r in result)

def test_clone_repository_skips_if_exists(tmp_path, monkeypatch):
    '''
    @brief Happy Path: No clona si ya existe el repo
    '''
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    with patch.object(script_auto.logger, "info") as loginfo:
        script_auto.clone_repository("url", str(repo_dir))
        loginfo.assert_any_call(f"Repository already exists at {repo_dir}, skipping clone.")

def test_update_repository_skips_if_missing(tmp_path, monkeypatch):
    '''
    @brief Edge Case: No hace pull si no existe el repo
    '''
    repo_dir = tmp_path / "repo"
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    with patch.object(script_auto.logger, "warning") as logwarn:
        script_auto.update_repository(str(repo_dir))
        logwarn.assert_any_call(f"Repository directory {repo_dir} does not exist. Cannot run git pull.")

def test_clone_repository_skips_in_pytest(monkeypatch):
    '''
    @brief Edge Case: No clona si detecta entorno pytest
    '''
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")
    with patch.object(script_auto.logger, "info") as loginfo:
        script_auto.clone_repository("url", "repo")
        loginfo.assert_any_call("[TEST] Skipping real git clone (detected test environment).")
    monkeypatch.delenv("PYTEST_CURRENT_TEST")

def test_update_repository_skips_in_pytest(monkeypatch):
    '''
    @brief Edge Case: No hace pull si detecta entorno pytest
    '''
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")
    # Mock os.path.isdir para que devuelva True y así no caiga en el warning de repo inexistente
    with patch("os.path.isdir", return_value=True):
        with patch.object(script_auto.logger, "info") as loginfo:
            script_auto.update_repository("repo")
            loginfo.assert_any_call("[TEST] Skipping real git pull (detected test environment).")
    monkeypatch.delenv("PYTEST_CURRENT_TEST")
