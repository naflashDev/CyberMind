import os
import json
import pytest

from app.services.llm import script_auto


def test_transform_json_minimal():
    # Provide a minimal CVE-like payload that `transform_json` understands.
    data = {
        "cveMetadata": {"state": "PUBLISHED", "cveId": "CVE-2026-0001", "datePublished": "2026-01-01"},
        "containers": {"cna": {"descriptions": [{"lang": "en", "value": "minimal description"}]}}
    }
    out = script_auto.transform_json(data)
    # transform_json returns a list of records for published CVEs
    assert isinstance(out, list)
    assert out and isinstance(out[0], dict) and 'instruction' in out[0]


def test_process_file_append(tmp_path):
    # Create a temporary input JSON file and use the internal worker to
    # transform it into the output path (mimics child-process behaviour).
    p = tmp_path / "out.json"
    in_file = tmp_path / "in.json"
    content = {
        "cveMetadata": {"state": "PUBLISHED", "cveId": "CVE-2026-0002"},
        "containers": {"cna": {"descriptions": [{"lang": "en", "value": "desc"}]}}
    }
    in_file.write_text(json.dumps(content), encoding="utf-8")
    # Call the module-level worker that writes transformed output to a path
    script_auto._process_file_worker(str(in_file), str(p))
    assert p.exists()
