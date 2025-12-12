from fastapi.testclient import TestClient
from app.utils.worker_control import default_settings

import app.controllers.routes.spacy_controller as spacy_mod
import app.controllers.routes.scrapy_news_controller as scrapy_mod
import app.controllers.routes.tiny_postgres_controller as tiny_mod


class DummyThread:
    def __init__(self, *args, **kwargs):
        self._target = kwargs.get('target') or (args[0] if args else None)
        self._args = kwargs.get('args') or (args[1] if len(args) > 1 else ())
        self.daemon = kwargs.get('daemon', True)

    def start(self):
        # do not actually start background work in tests
        return None


def test_status_includes_all_workers():
    from main import app
    client = TestClient(app)
    resp = client.get('/status')
    assert resp.status_code == 200
    data = resp.json()
    assert 'workers' in data
    workers = data['workers']
    expected_keys = set(default_settings().keys())
    assert expected_keys.issubset(set(workers.keys()))


def test_start_spacy_marks_worker(monkeypatch):
    from main import app
    # prevent actual threads from starting
    monkeypatch.setattr(spacy_mod.threading, 'Thread', DummyThread)
    client = TestClient(app)
    # ensure inputs exist for spacy
    import os
    out_dir = './outputs'
    input_path = os.path.join(out_dir, 'result.json')
    created = False
    if not os.path.exists(input_path):
        os.makedirs(out_dir, exist_ok=True)
        with open(input_path, 'w', encoding='utf-8') as f:
            f.write('[]')
        created = True

    resp = client.get('/start-spacy')
    assert resp.status_code == 200
    # response no longer includes 'workers'; query /status for worker states
    status_resp = client.get('/status')
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert 'workers' in status_data
    assert status_data['workers'].get('spacy_nlp', False) is True
    if created:
        try:
            os.remove(input_path)
        except Exception:
            pass


def test_start_rss_marks_worker(monkeypatch):
    from main import app
    monkeypatch.setattr(tiny_mod.threading, 'Thread', DummyThread)
    client = TestClient(app)
    # ensure urls file exists; if not, create a temp one
    import os
    path = './data/urls_cybersecurity_ot_it.txt'
    created = False
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write('https://example.com/feed')
        created = True

    # ensure app has a pool attribute to avoid AttributeError in test
    app.state.pool = object()
    resp = client.get('/postgre-ttrss/search-and-insert-rss')
    # cleanup
    if created:
        try:
            os.remove(path)
        except Exception:
            pass

    assert resp.status_code == 200
    # response no longer includes workers; check /status
    status_resp = client.get('/status')
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert 'workers' in status_data
    assert status_data['workers'].get('rss_extractor', False) is True
