from fastapi.testclient import TestClient


def test_ui_contains_controllers():
    from main import app
    client = TestClient(app)
    resp = client.get('/ui')
    assert resp.status_code == 200
    text = resp.text
    assert 'const controllers = {' in text
