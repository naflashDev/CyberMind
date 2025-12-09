"""
@file status_controller.py
@brief Run dependent services.
@details This script ensures that the required infrastructure services
(OpenSearch, Dashboards, and Tiny RSS Docker container) are running inside
a specified distribution before launching the FastAPI application.
@date Created: 2025-11-27 12:17:59
@author naflashDev
@project CyberMind
"""

from fastapi import APIRouter, Request

router = APIRouter(
    prefix="",
    tags=["Status"],
)


@router.get("/status")
async def get_status(request: Request):
    """Return basic system status: infra readiness and worker booleans."""
    app = request.app
    infra_ready = getattr(app.state, "infra_ready", False)
    infra_error = getattr(app.state, "infra_error", None)
    ui_initialized = getattr(app.state, "ui_initialized", False)
    workers = getattr(app.state, "worker_status", {}) or {}
    simple_workers = {k: bool(v) for k, v in workers.items()}
    return {
        "infra_ready": bool(infra_ready),
        "infra_error": infra_error,
        "ui_initialized": bool(ui_initialized),
        "workers": simple_workers,
    }
