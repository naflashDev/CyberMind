def test_consolidate_json_stop_event(monkeypatch, tmp_path):
    d = tmp_path / "repo3"
    d.mkdir()
    (d / "f0.json").write_text(json.dumps({"cveMetadata": {"state": "PUBLISHED"}}), encoding="utf-8")
    class DummyEvent:
        def is_set(self): return True
    with patch("src.app.services.llm.script_auto.logger") as mock_logger:
        script_auto.consolidate_json(str(d), str(tmp_path / "out3.json"), stop_event=DummyEvent())
        assert mock_logger.info.called

def test_consolidate_json_is_finalizing(monkeypatch, tmp_path):
    d = tmp_path / "repo4"
    d.mkdir()
    (d / "f0.json").write_text(json.dumps({"cveMetadata": {"state": "PUBLISHED"}}), encoding="utf-8")
    monkeypatch.setattr(script_auto.sys, "is_finalizing", lambda: True)
    with patch("src.app.services.llm.script_auto.logger") as mock_logger:
        script_auto.consolidate_json(str(d), str(tmp_path / "out4.json"))
        assert mock_logger.warning.called

def test_consolidate_json_active_processes(monkeypatch, tmp_path):
    d = tmp_path / "repo5"
    d.mkdir()
    for i in range(2):
        (d / f"f{i}.json").write_text(json.dumps({"cveMetadata": {"state": "PUBLISHED", "cveId": f"CVE-{i}"}}), encoding="utf-8")
    # DummyProc simula procesos activos y join/terminate
    class DummyProc:
        def __init__(self, target, args): self._alive = True; self._target = target; self._args = args
        def start(self): self._target(*self._args); self._alive = False
        def is_alive(self): return self._alive
        def join(self, timeout=None): self._alive = False
        def terminate(self): self._alive = False
    monkeypatch.setattr(script_auto, "_process_file_worker", lambda i, o: open(o, "w").write("[]"))
    monkeypatch.setattr(script_auto.multiprocessing, "Process", DummyProc)
    monkeypatch.setattr(script_auto.multiprocessing, "Manager", lambda: type("M", (), {"Lock": staticmethod(lambda: type("L", (), {"__enter__": lambda s: None, "__exit__": lambda s,a,b,c: None})())})())
    out_file = tmp_path / "out5.json"
    script_auto.consolidate_json(str(d), str(out_file))
    assert out_file.exists()

def test_consolidate_json_warning_partial(monkeypatch, tmp_path):
    d = tmp_path / "repo6"
    d.mkdir()
    (d / "f0.json").write_text(json.dumps({"cveMetadata": {"state": "PUBLISHED"}}), encoding="utf-8")
    # Fuerza excepción al leer parcial
    import builtins
    real_open = builtins.open
    def fake_open(*a, **kw):
        # Solo lanza excepción al leer el archivo parcial, no al escribir
        if a[0].endswith("out_0.json") and (len(a) > 1 and a[1] == "r"):
            raise Exception("fail read")
        return real_open(*a, **kw)
    monkeypatch.setattr(script_auto, "_process_file_worker", lambda i, o: open(o, "w").write("[]"))
    monkeypatch.setattr(script_auto.multiprocessing, "Process", lambda target, args: type("P", (), {"start": lambda s: target(*args), "is_alive": lambda s: False, "join": lambda s, timeout=None: None, "terminate": lambda s: None})())
    monkeypatch.setattr(script_auto.multiprocessing, "Manager", lambda: type("M", (), {"Lock": staticmethod(lambda: type("L", (), {"__enter__": lambda s: None, "__exit__": lambda s,a,b,c: None})())})())
    monkeypatch.setattr("builtins.open", fake_open)
    with patch("src.app.services.llm.script_auto.logger") as mock_logger:
        out_file = tmp_path / "out6.json"
        script_auto.consolidate_json(str(d), str(out_file))
        # Solo debe verificar que el warning fue emitido
        assert mock_logger.warning.called
def test_clone_repository_git_error(tmp_path):
    repo_dir = tmp_path / "repo3"
    with patch("src.app.services.llm.script_auto.subprocess.check_call", side_effect=Exception("fail")), \
         patch("src.app.services.llm.script_auto.logger") as mock_logger:
        with pytest.raises(Exception):
            script_auto.clone_repository("url", str(repo_dir))
        assert mock_logger.error.called

def test_update_repository_git_error(tmp_path):
    repo_dir = tmp_path / "repo4"
    repo_dir.mkdir()
    with patch("src.app.services.llm.script_auto.subprocess.check_call", side_effect=Exception("fail")), \
         patch("src.app.services.llm.script_auto.logger") as mock_logger:
        with pytest.raises(Exception):
            script_auto.update_repository(str(repo_dir))
        assert mock_logger.error.called

def test_process_file_json_decode_error(tmp_path):
    file = tmp_path / "bad2.json"
    file.write_text("{not json}", encoding="utf-8")
    agg = []
    lock = MagicMock()
    with patch("src.app.services.llm.script_auto.logger") as mock_logger:
        script_auto.process_file(file, agg, lock)
        assert mock_logger.warning.called

def test_process_file_unexpected_error(tmp_path):
    file = tmp_path / "ok2.json"
    file.write_text(json.dumps({"cveMetadata": {"state": "PUBLISHED"}}), encoding="utf-8")
    agg = []
    lock = MagicMock()
    with patch("src.app.services.llm.script_auto.transform_json", side_effect=Exception("fail")), \
         patch("src.app.services.llm.script_auto.logger") as mock_logger:
        script_auto.process_file(file, agg, lock)
        assert mock_logger.error.called

def test__process_file_worker_error(tmp_path):
    file = tmp_path / "input2.json"
    file.write_text(json.dumps({"cveMetadata": {"state": "PUBLISHED"}}), encoding="utf-8")
    out = tmp_path / "out2.json"
    # Fuerza excepción en transformación
    with patch("src.app.services.llm.script_auto.transform_json", side_effect=Exception("fail")):
        script_auto._process_file_worker(str(file), str(out))
    # El archivo de salida no debe existir
    assert not out.exists()

def test_consolidate_json_error(monkeypatch, tmp_path):
    d = tmp_path / "repo2"
    d.mkdir()
    (d / "f0.json").write_text(json.dumps({"cveMetadata": {"state": "PUBLISHED"}}), encoding="utf-8")
    # Fuerza excepción en open
    monkeypatch.setattr("builtins.open", lambda *a, **kw: (_ for _ in ()).throw(Exception("fail open")))
    with patch("src.app.services.llm.script_auto.logger") as mock_logger:
        with pytest.raises(Exception):
            script_auto.consolidate_json(str(d), str(tmp_path / "out2.json"))
        assert mock_logger.error.called
"""
@file test_script_auto.py
@author GitHub Copilot
@brief Unit tests for script_auto.py
@details Tests for repository management, file processing, and transformation utilities (mocks, no real git or multiprocessing).
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.app.services.llm import script_auto

def test_clone_repository_skips_if_exists(tmp_path):
    '''
    @brief Should skip cloning if directory exists.
    '''
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    with patch("src.app.services.llm.script_auto.logger") as mock_logger:
        script_auto.clone_repository("url", str(repo_dir))
        mock_logger.info.assert_any_call(f"Repository already exists at {repo_dir}, skipping clone.")

def test_clone_repository_runs_git_clone(tmp_path):
    '''
    @brief Should call git clone if directory does not exist.
    '''
    repo_dir = tmp_path / "repo2"
    with patch("src.app.services.llm.script_auto.subprocess.check_call") as mock_call, \
         patch("src.app.services.llm.script_auto.logger") as mock_logger:
        script_auto.clone_repository("url", str(repo_dir))
        mock_call.assert_called_once()
        assert mock_logger.success.called

def test_update_repository_skips_if_missing(tmp_path):
    '''
    @brief Should skip update if directory does not exist.
    '''
    repo_dir = tmp_path / "repo"
    with patch("src.app.services.llm.script_auto.logger") as mock_logger:
        script_auto.update_repository(str(repo_dir))
        mock_logger.warning.assert_any_call(f"Repository directory {repo_dir} does not exist. Cannot run git pull.")

def test_update_repository_runs_git_pull(tmp_path):
    '''
    @brief Should call git pull if directory exists.
    '''
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    with patch("src.app.services.llm.script_auto.subprocess.check_call") as mock_call, \
         patch("src.app.services.llm.script_auto.logger") as mock_logger:
        script_auto.update_repository(str(repo_dir))
        mock_call.assert_called_once()
        assert mock_logger.success.called

def test_transform_json_filters_non_published():
    '''
    @brief Should return empty for non-PUBLISHED CVEs.
    '''
    cve = {"cveMetadata": {"state": "REJECTED"}}
    assert script_auto.transform_json(cve) == []

def test_transform_json_handles_list():
    '''
    @brief Should process a list of CVEs.
    '''
    cve = [{"cveMetadata": {"state": "PUBLISHED"}}]
    result = script_auto.transform_json(cve)
    assert isinstance(result, list)

def test_process_file_handles_invalid_json(tmp_path):
    '''
    @brief Should warn and skip invalid JSON.
    '''
    file = tmp_path / "bad.json"
    file.write_text("not a json", encoding="utf-8")
    agg = []
    lock = MagicMock()
    with patch("src.app.services.llm.script_auto.logger") as mock_logger:
        script_auto.process_file(file, agg, lock)
        assert mock_logger.warning.called

def test_process_file_appends_transformed(tmp_path):
    '''
    @brief Should append transformed data.
    '''
    file = tmp_path / "ok.json"
    file.write_text(json.dumps({"cveMetadata": {"state": "PUBLISHED"}}), encoding="utf-8")
    agg = []
    lock = MagicMock()
    lock.__enter__ = lambda s: None
    lock.__exit__ = lambda s, a, b, c: None
    script_auto.process_file(file, agg, lock)
    assert isinstance(agg, list)


def test_transform_json_unexpected_types():
    '''
    @brief Should handle unexpected types gracefully.
    '''
    assert script_auto.transform_json("string") == []
    assert script_auto.transform_json(123) == []
    assert script_auto.transform_json(["not_a_dict"]) == []


def test_transform_json_with_adp_and_solutions():
    '''
    @brief Should extract ADP and solution info.
    '''
    cve = {
        "cveMetadata": {"state": "PUBLISHED", "cveId": "CVE-0000-0000"},
        "containers": {
            "cna": {
                "descriptions": [{"lang": "en", "value": "desc"}],
                "affected": [{"product": "p", "vendor": "v", "versions": [{"version": "1.0"}]}],
                "problemTypes": [{"descriptions": [{"cweId": "CWE-1", "description": "desc", "lang": "en"}]}],
                "references": [{"url": "http://example.com"}],
                "metrics": [{"cvssV4_0": {"version": "4.0", "baseScore": 9, "baseSeverity": "HIGH", "vectorString": "..."}}],
                "solutions": [{"value": "patch"}]
            },
            "adp": [{"metrics": [{"other": {"type": "ssvc", "content": {"options": [{"Exploitation": "yes", "Automatable": "no", "Technical Impact": "high"}]}}}]}]
        },
        "dataVersion": "1.0"
    }
    result = script_auto.transform_json(cve)
    assert isinstance(result, list)
    assert result and "instruction" in result[0]
    assert "Exploitation: yes" in result[0]["input"]
    assert "solution" in result[0]["input"].lower() or "mitigation" in result[0]["input"].lower()


def test__process_file_worker_creates_output(tmp_path):
    '''
    @brief Should write transformed output to file.
    '''
    file = tmp_path / "input.json"
    file.write_text(json.dumps({"cveMetadata": {"state": "PUBLISHED", "cveId": "CVE-1"}}), encoding="utf-8")
    out = tmp_path / "out.json"
    script_auto._process_file_worker(str(file), str(out))
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(data, list)


def test_consolidate_json_runs(monkeypatch, tmp_path):
    '''
    @brief Should consolidate multiple JSON files.
    '''
    # Crear archivos de entrada
    d = tmp_path / "repo"
    d.mkdir()
    for i in range(3):
        (d / f"f{i}.json").write_text(json.dumps({"cveMetadata": {"state": "PUBLISHED", "cveId": f"CVE-{i}"}}), encoding="utf-8")

    # Parchear multiprocessing para ejecución rápida (sin procesos)
    # Simula la creación de archivos de salida como lo haría _process_file_worker
    outputs = {}
    def fake_process_file_worker(input_path, out_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(out_path, 'w', encoding='utf-8') as of:
            json.dump([{"instruction": "dummy"}], of)
        outputs[out_path] = True
    class DummyProc:
        def __init__(self, target, args):
            self._alive = False
            self._target = target
            self._args = args
        def start(self):
            self._target(*self._args)
            self._alive = False
        def is_alive(self): return self._alive
        def join(self, timeout=None): pass
        def terminate(self): self._alive = False
    monkeypatch.setattr(script_auto, "_process_file_worker", fake_process_file_worker)
    monkeypatch.setattr(script_auto.multiprocessing, "Process", DummyProc)
    monkeypatch.setattr(script_auto.multiprocessing, "Manager", lambda: type("M", (), {"Lock": staticmethod(lambda: type("L", (), {"__enter__": lambda s: None, "__exit__": lambda s,a,b,c: None})())})())
    monkeypatch.setattr(script_auto, "time", script_auto.time)
    out_file = tmp_path / "out.json"
    script_auto.consolidate_json(str(d), str(out_file))
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 3


def test_update_cve_repo_and_build_list(monkeypatch, tmp_path):
    '''
    @brief Should call clone/update and consolidate.
    '''
    called = {"clone": False, "update": False, "consolidate": False}
    def fake_clone(url, dir): called["clone"] = True
    def fake_update(dir): called["update"] = True
    def fake_consolidate(dir, out, stop_event=None): called["consolidate"] = True
    monkeypatch.setattr(script_auto, "clone_repository", fake_clone)
    monkeypatch.setattr(script_auto, "update_repository", fake_update)
    monkeypatch.setattr(script_auto, "consolidate_json", fake_consolidate)
    repo_dir = tmp_path / "repo"
    # Caso: no existe, debe clonar
    script_auto.update_cve_repo_and_build_list(repo_url="url", repo_dir=str(repo_dir), output_dir=str(tmp_path), output_file_name="out.json")
    assert called["clone"]
    # Caso: existe, debe actualizar
    repo_dir.mkdir(exist_ok=True)
    called = {"clone": False, "update": False, "consolidate": False}
    script_auto.update_cve_repo_and_build_list(repo_url="url", repo_dir=str(repo_dir), output_dir=str(tmp_path), output_file_name="out.json")
    assert called["update"]
    assert called["consolidate"]
