from fastapi import FastAPI
from fastapi.testclient import TestClient

# Create a minimal app and mount only the status router so we avoid importing heavy deps
from src.app.controllers.routes import status_controller

app = FastAPI()
app.include_router(status_controller.router)

# ensure some default state for demonstration
app.state.infra_ready = False
app.state.infra_error = None
app.state.ui_initialized = False
app.state.worker_status = {"llm_updater": False}

client = TestClient(app)
resp = client.get('/status')
print('Status code:', resp.status_code)
print('Body:', resp.json())
