from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from loguru import logger
import threading

from app.utils.worker_control import load_worker_settings, save_worker_settings
from app.controllers.routes import (
    scrapy_news_controller,
    spacy_controller,
    tiny_postgres_controller,
    llm_controller,
)
import asyncpg

router = APIRouter(prefix="/workers", tags=["workers"])


class WorkerToggle(BaseModel):
    enabled: bool


@router.get("")
async def get_workers(request: Request):
    settings = load_worker_settings()
    status = getattr(request.app.state, "worker_status", {}) or {}
    # ensure all known workers are present
    combined = {k: bool(status.get(k, False)) for k in settings.keys()}
    for k, v in status.items():
        if k not in combined:
            combined[k] = bool(v)
    return {"settings": settings, "status": combined}


@router.post("/{name}")
async def toggle_worker(name: str, payload: WorkerToggle, request: Request):
    settings = load_worker_settings()
    if name not in settings:
        raise HTTPException(status_code=404, detail="Unknown worker")

    settings[name] = bool(payload.enabled)
    # persist
    save_worker_settings(settings)

    # Ensure app state dicts exist
    if getattr(request.app.state, "worker_stop_events", None) is None:
        request.app.state.worker_stop_events = {}
    if getattr(request.app.state, "worker_timers", None) is None:
        request.app.state.worker_timers = {}
    if getattr(request.app.state, "worker_status", None) is None:
        request.app.state.worker_status = {}

    # If disabling => signal stop_event and cancel timer
    if not settings[name]:
        evt = request.app.state.worker_stop_events.get(name)
        if evt is not None:
            try:
                evt.set()
            except Exception:
                pass
        timer = request.app.state.worker_timers.get(name)
        if timer is not None:
            try:
                # if stored object is a threading.Timer or asyncio.Task it may support cancel()
                if hasattr(timer, 'cancel'):
                    try:
                        timer.cancel()
                    except Exception:
                        pass
                # if stored object is a multiprocessing.Process, terminate it
                elif hasattr(timer, 'terminate'):
                    try:
                        timer.terminate()
                        timer.join(timeout=2)
                    except Exception:
                        pass
            except Exception:
                pass
        request.app.state.worker_status[name] = False
        logger.info(f"Worker {name} disabled via UI.")
        return {"message": f"Worker {name} disabled"}

    # Enabling: start worker similar to initialization
    # create stop event
    evt = threading.Event()
    request.app.state.worker_stop_events[name] = evt

    def _register_timer(t):
        request.app.state.worker_timers[name] = t

    loop = None
    try:
        import asyncio
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    # start according to worker name
    if name == "google_alerts":
        feeds_path = "./data/google_alert_rss.txt"
        if not __import__("os").path.exists(feeds_path):
            raise HTTPException(status_code=400, detail="feeds file missing")
        threading.Thread(target=scrapy_news_controller.recurring_google_alert_scraper, args=(loop, evt, _register_timer), daemon=True).start()
    elif name == "rss_extractor":
        file_path = "./data/urls_cybersecurity_ot_it.txt"
        pool = getattr(request.app.state, "pool", None)
        if not __import__("os").path.exists(file_path):
            raise HTTPException(status_code=400, detail="urls file missing")
        threading.Thread(target=tiny_postgres_controller.background_rss_process_loop, args=(pool, file_path, loop, evt, _register_timer), daemon=True).start()
    elif name == "scraping_feeds":
        threading.Thread(target=scrapy_news_controller.background_scraping_feeds, args=(loop, evt, _register_timer), daemon=True).start()
    elif name == "scraping_news":
        threading.Thread(target=scrapy_news_controller.background_scraping_news, args=(loop, evt, _register_timer), daemon=True).start()
    elif name == "spacy_nlp":
        input_path = "./outputs/result.json"
        output_path = "./outputs/labels_result.json"
        if not __import__("os").path.exists(input_path):
            raise HTTPException(status_code=400, detail="input file missing")
        threading.Thread(target=spacy_controller.background_process_every_24h, args=(input_path, output_path, evt, _register_timer), daemon=True).start()
    elif name == "llm_updater":
        threading.Thread(target=llm_controller.background_cve_and_finetune_loop, args=(evt,), daemon=True).start()
    elif name == "dynamic_spider":
        pool = getattr(request.app.state, "pool", None)
        # Try to create pool on-demand if not present (UI may trigger init asynchronously)
        if pool is None:
            try:
                pool = await asyncpg.create_pool(
                    user="postgres",
                    password="password123",
                    database="postgres",
                    host="127.0.0.1",
                    port=5432,
                    min_size=1,
                    max_size=5,
                )
                request.app.state.pool = pool
            except Exception:
                raise HTTPException(status_code=503, detail="DB pool not available and on-demand creation failed")
        import asyncio
        # pass stop_event and register callback so UI can control the process
        asyncio.create_task(scrapy_news_controller.run_dynamic_spider_from_db(pool, stop_event=evt, register_process=_register_timer))
    else:
        raise HTTPException(status_code=400, detail="Unsupported worker")

    request.app.state.worker_status[name] = True
    logger.info(f"Worker {name} enabled via UI.")
    return {"message": f"Worker {name} enabled"}
