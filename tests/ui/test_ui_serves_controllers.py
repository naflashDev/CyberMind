from fastapi.testclient import TestClient


def test_ui_contains_controllers():
    from main import app
    client = TestClient(app)
    # The controllers object is now served inside the external UI script
    resp = client.get('/ui/ui.js')
    assert resp.status_code == 200
    text = resp.text
    assert 'const controllers = {' in text
