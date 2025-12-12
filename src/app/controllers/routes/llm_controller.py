"""
@file llm_controller.py
@author naflashDev
@brief FastAPI routes to interact with the remote LLM.
@details Provides HTTP endpoints for programmatic and UI-based queries.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from loguru import logger
from app.services.llm.llm_client import query_llm
from app.services.llm.llm_trainer import run_periodic_training
from typing import Optional
import threading


class UpdaterToggle(BaseModel):
    enabled: bool

router = APIRouter(prefix="/llm", tags=["llm"])


class LLMQuery(BaseModel):
    """
    @brief Request model for LLM query endpoint.
    """
    prompt: str


@router.post("/query")
async def llm_query(payload: LLMQuery):
    """
    @brief Receives a prompt and returns the LLM response.
    @param payload JSON body with a 'prompt' field.
    @return JSON object containing 'response' string.
    """
    response = query_llm(payload.prompt)
    logger.debug(f"[LLM Client] Sending response to the user.")
    return {"response": response}

def background_cve_and_finetune_loop(stop_event: Optional[threading.Event] = None) -> None:
    """
    @brief Background loop to update CVE repo and rebuild LLM dataset every 7 days.
    @details
        - Calls run_periodic_training() once per cycle.
        - Sleeps for 7 days (7 * 24 * 60 * 60 seconds) between executions.
    """
    import time
    from loguru import logger

    interval = 7 * 24 * 60 * 60  # 7 days
    # If no stop_event provided, create a dummy one to keep compatibility
    if stop_event is None:
        stop_event = threading.Event()

    while not stop_event.is_set():
        try:
            logger.info("[LLM Trainer] Starting 7-day CVE update + dataset build cycle...")
            run_periodic_training(stop_event=stop_event)
            logger.info("[LLM Trainer] 7-day CVE + dataset cycle finished.")
        except Exception as e:
            logger.error(f"[LLM Trainer] Error in 7-day loop: {e}")
        # Wait in an interruptible way so shutdown can proceed quickly
        try:
            stop_event.wait(interval)
        except Exception:
            # If wait fails for any reason, fallback to sleep a short time then re-check
            time.sleep(5)



@router.get('/updater')
async def updater_get(request: Request):
    """Start the LLM updater background loop via GET (compatible with other GET starters)."""
    # ensure app.state dicts
    if getattr(request.app.state, 'worker_stop_events', None) is None:
        request.app.state.worker_stop_events = {}
    if getattr(request.app.state, 'worker_timers', None) is None:
        request.app.state.worker_timers = {}
    if getattr(request.app.state, 'worker_status', None) is None:
        request.app.state.worker_status = {}

    name = 'llm_updater'
    if request.app.state.worker_status.get(name):
        return {"message": f"Worker {name} already running"}

    evt = threading.Event()
    request.app.state.worker_stop_events[name] = evt
    th = threading.Thread(target=background_cve_and_finetune_loop, args=(evt,), daemon=True)
    th.start()
    request.app.state.worker_timers[name] = th
    request.app.state.worker_status[name] = True
    logger.info(f"[LLM] Updater started via /llm/updater")
    return {"message": "LLM updater started"}


@router.get('/stop-updater')
async def stop_updater(request: Request):
    """Stop the LLM updater background loop (GET endpoint)."""
    name = 'llm_updater'
    if getattr(request.app.state, 'worker_stop_events', None) is None:
        request.app.state.worker_stop_events = {}
    if getattr(request.app.state, 'worker_timers', None) is None:
        request.app.state.worker_timers = {}
    if getattr(request.app.state, 'worker_status', None) is None:
        request.app.state.worker_status = {}

    evt = request.app.state.worker_stop_events.get(name)
    if evt is not None:
        try:
            evt.set()
        except Exception:
            pass

    timer = request.app.state.worker_timers.get(name)
    if timer is not None:
        try:
            if hasattr(timer, 'cancel'):
                timer.cancel()
        except Exception:
            pass

    request.app.state.worker_status[name] = False
    logger.info(f"[LLM] Updater stopped via /llm/stop-updater")
    return {"message": "LLM updater stopped"}
