"""
@file status_controller.py
@author naflashDev
@brief System status endpoints.
@details Exposes a lightweight `GET /status` endpoint used by the UI to determine infra readiness, UI initialization, and the enabled/disabled state of background workers. Combines persisted defaults with runtime values for a complete status response.
"""


from fastapi import APIRouter, Request
from app.utils.worker_control import default_settings

router = APIRouter(
    prefix="",
    tags=["Status"],
)


@router.get("/status")
async def get_status(request: Request):
    """
    @brief Return basic system status for the UI.
    @details Returns a JSON object with `infra_ready`, `infra_error`,
    `ui_initialized` and `workers` fields. `workers` is a mapping of known
    worker names to booleans (ensured by merging defaults and runtime
    status).
    """
    app = request.app
    infra_ready = getattr(app.state, "infra_ready", False)
    infra_error = getattr(app.state, "infra_error", None)
    ui_initialized = getattr(app.state, "ui_initialized", False)
    workers = getattr(app.state, "worker_status", {}) or {}
    # ensure all known workers are present in the returned dict
    all_keys = list(default_settings().keys())
    combined = {k: bool(workers.get(k, False)) for k in all_keys}
    # include any extra dynamic keys as well
    for k, v in workers.items():
        if k not in combined:
            combined[k] = bool(v)

    return {
        "infra_ready": bool(infra_ready),
        "infra_error": infra_error,
        "ui_initialized": bool(ui_initialized),
        "workers": combined,
    }
