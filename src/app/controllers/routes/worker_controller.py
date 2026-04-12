
"""
@file worker_controller.py
@brief HTTP endpoints to inspect and toggle background workers.
@details Exposes `GET /workers` to return persisted settings and runtime
status, and `POST /workers/{name}` to enable/disable named background
workers. When enabling a worker the endpoint creates a stop event and
registers timers/process objects so the UI can control them. When disabling
it signals the stop event and attempts to cancel or terminate running
background tasks.
@author naflashDev
"""


# Standard library imports
import os
import signal
import threading
from pathlib import Path
import time
import inspect


# Third-party imports
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Response
from pydantic import BaseModel
from loguru import logger
import asyncpg
from dotenv import load_dotenv
import asyncio

# Internal imports
from app.utils.worker_control import load_worker_settings, save_worker_settings
from app.controllers.routes import (
    scrapy_news_controller,
    spacy_controller,
    tiny_postgres_controller,
    llm_controller,
)
from app.utils.run_services import shutdown_services

router = APIRouter(prefix="/workers", tags=["workers"])


class WorkerToggle(BaseModel):
    enabled: bool

@router.post("/shutdown")
async def shutdown_app(background_tasks: BackgroundTasks, request: Request):
    '''
    @brief Shutdown the backend and all subprocesses.

    This endpoint triggers a safe shutdown of the FastAPI app and all background workers/processes.
    It returns immediately to the client, then kills the process in the background.

    @param background_tasks BackgroundTasks for deferred kill.
    @param request FastAPI Request object.
    @return JSON message indicating shutdown was triggered.
    '''
    # Señal de log y respuesta inmediata
    logger.warning("[API] Shutdown endpoint called. App will terminate.")
    # Defer kill to background to allow HTTP response
    def kill_proc():
        # 1. Señalizar eventos de parada de workers
        try:
            app = request.app
            stop_event = getattr(app.state, "stop_event", None)
            if stop_event is not None:
                try:
                    stop_event.set()
                except Exception:
                    pass
            stop_events = getattr(app.state, "worker_stop_events", {})
            for evt in stop_events.values():
                try:
                    evt.set()
                except Exception:
                    pass
            timers = getattr(app.state, "worker_timers", {})
            for t in timers.values():
                try:
                    if hasattr(t, 'cancel'):
                        t.cancel()
                    elif hasattr(t, 'terminate'):
                        t.terminate()
                        if hasattr(t, 'join'):
                            t.join(timeout=2)
                except Exception:
                    pass
            # 2. Marcar workers como parados
            ws = getattr(app.state, "worker_status", None)
            if isinstance(ws, dict):
                for k in list(ws.keys()):
                    ws[k] = False
                app.state.worker_status = ws
            # 3. Cerrar pool de PostgreSQL si existe
            pool = getattr(app.state, "pool", None)
            if pool:
                try:
                    loop = None
                    try:
                        loop = asyncio.get_running_loop()
                    except Exception:
                        pass
                    if loop and loop.is_running():
                        fut = pool.close()
                        if hasattr(fut, '__await__'):
                            loop.run_until_complete(fut)
                    else:
                        # fallback sync
                        pool.close()
                except Exception:
                    pass
            # 4. Apagar servicios externos (compose, ollama)
            try:
                project_root = Path(__file__).resolve().parents[3]
                distro_arg = None
                containers_arg = None
                try:
                    parameters = getattr(app.state, 'parameters', None)
                    if parameters:
                        distro_arg = parameters[0] if len(parameters) > 0 else None
                        containers_arg = parameters[1] if len(parameters) > 1 else None
                except Exception:
                    pass
                shutdown_services(
                    project_root=project_root,
                    stop_ollama=True,
                    force_stop_containers=True,
                    distro_name=distro_arg,
                    containers=containers_arg,
                )
            except Exception:
                pass
        except Exception:
            pass
        # Espera breve para que los workers paren y los logs se vacíen
        time.sleep(0.5)
        # Log shutdown success message in English
        try:
            logger.success("App shutdown completed successfully. You may now close this console.")
        except Exception:
            pass
        # Cerrar el logger explícitamente
        try:
            logger.remove()
        except Exception:
            pass
        # Forzar salida inmediata
        os._exit(0)
    background_tasks.add_task(kill_proc)
    # Add 'reload' field to signal frontend to reload UI
    return {
        "message": "Apagado iniciado. La aplicación se cerrará en unos segundos.",
        "reload": True
    }

@router.get("")
async def get_workers(request: Request):
    """
    @brief Return known worker settings and runtime status.
    @details Loads persisted worker settings and combines them with the
    current runtime `app.state.worker_status` mapping so the response
    always contains the full set of known workers. Useful for the UI
    to display toggles and their current state.
    """
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
    """
    @brief Enable or disable a named worker.
    @details Persists the requested state, creates or signals a
    `threading.Event` used to stop background loops, and starts or stops
    the corresponding background thread/process according to `name`.
    Returns a simple message indicating the result.

    Args:
        name: The worker identifier (must be present in default settings).
        payload: JSON body containing `enabled: bool`.
        request: FastAPI Request object (used to access app.state).
    """
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
            env_test = Path(__file__).parent.parent.parent.parent / ".env.test"
            if env_test.exists():
                load_dotenv(dotenv_path=env_test)
            else:
                load_dotenv()
            try:
                pool = await asyncpg.create_pool(
                    user=os.getenv("POSTGRES_USER"),
                    password=os.getenv("POSTGRES_PASSWORD"),
                    database=os.getenv("POSTGRES_DB"),
                    host=os.getenv("POSTGRES_HOST"),
                    port=int(os.getenv("POSTGRES_PORT", 5432)),
                    min_size=1,
                    max_size=5,
                )
                request.app.state.pool = pool
                logger.info("[dynamic_spider] PostgreSQL pool created on-demand successfully.")
            except Exception as e:
                logger.error(f"[dynamic_spider] Failed to create DB pool: {e}")
                request.app.state.worker_status[name] = False
                # Generic error message for UI, no internal details
                return Response(status_code=503, content="Ha ocurrido un error interno. Por favor, contacte con el administrador.")
        try:
            # pass stop_event and register callback so UI can control the process
            # Para evitar RuntimeWarning en tests y ejecución, comprobamos si la corutina es awaitable y si hay event loop
            coro = scrapy_news_controller.run_dynamic_spider_from_db(pool, stop_event=evt, register_process=_register_timer)
            try:
                loop = asyncio.get_running_loop()
                # Si hay event loop, lanzamos como tarea
                asyncio.create_task(coro)
            except RuntimeError:
                # Si no hay event loop (ejecución síncrona o test), simplemente ignora la tarea
                pass
            logger.info("[dynamic_spider] Worker launched successfully.")
        except Exception as e:
            logger.error(f"[dynamic_spider] Failed to launch worker: {e}")
            request.app.state.worker_status[name] = False
            # Generic error message for UI, no internal details
            return Response(status_code=503, content="Ha ocurrido un error interno. Por favor, contacte con el administrador.")

    # Additional workers that can be started on-demand via the same endpoint
    elif name == "vector_retention":
        # Start the retention worker dynamically (purge old vectors and DB messages)
        try:
            mod = __import__("app.services.retention.retention_worker", fromlist=["vector_and_message_retention"])
            target_fn = getattr(mod, "vector_and_message_retention")
            threading.Thread(target=target_fn, args=(evt, 7, 24), daemon=True).start()
            logger.info("[worker_controller] vector_retention started via UI")
        except Exception:
            logger.exception("[worker_controller] Failed to start vector_retention")
            request.app.state.worker_status[name] = False
            return {"message": "Failed to start vector_retention"}

    elif name == "vector_ingest":
        # Periodically scan data/documents and ingest files into the vectorstore
        folder = "./data/documents"
        interval_hours = 24

        def vector_ingest_loop(stop_evt, ingest_folder, hours):
            # Lazy imports inside loop to avoid import-time overhead in tests
            from hashlib import sha256
            try:
                while not stop_evt.is_set():
                    try:
                        # Try to construct a Chroma client if available to check existing ids
                        chroma_client = None
                        try:
                            from app.services.vectorstore.chroma_client import ChromaClient
                            chroma_client = ChromaClient(embed_model=None)
                        except Exception:
                            chroma_client = None

                        from app.services.documents import ingest as ingest_service
                        ingest_document = ingest_service.ingest_document

                        for root, dirs, files in __import__("os").walk(ingest_folder):
                            # Skip known repo metadata directories (e.g., .github)
                            try:
                                # Exclude common VCS and repo metadata folders from scanning
                                # e.g., .github and .git so we don't traverse hidden repo data
                                dirs[:] = [d for d in dirs if d.lower() not in ('.github', '.git')]
                            except Exception:
                                pass

                            for fname in files:
                                # Ignore blacklisted files (delta files, readmes, git metadata)
                                try:
                                    if ingest_service.is_blacklisted_filename(fname):
                                        continue
                                except Exception:
                                    # if blacklist check fails, fall back to previous behavior
                                    if fname.lower() in ("delta.json", "deltalog.json"):
                                        continue

                                path = __import__("os").path.join(root, fname)
                                try:
                                    with open(path, 'rb') as rf:
                                        content = rf.read()
                                except Exception:
                                    continue
                                # If this looks like a CVE JSON file inside a CVE repo tree,
                                # index it in-place (no copy into data/documents).
                                try:
                                    lower_root = root.replace('\\', '/').lower()
                                    is_cve_json = fname.lower().endswith('.json') and (('/cves/' in lower_root) or ('cve' in lower_root) or ('cvelist' in lower_root))
                                except Exception:
                                    is_cve_json = False
                                # compute stable doc_id using the same filename sanitization
                                # as `ingest_document` (spaces -> underscores) to ensure
                                # consistent ids and avoid duplicate upserts.
                                safe_name = (fname or '').replace(' ', '_')
                                h = sha256()
                                h.update(content or b"")
                                h.update((safe_name or "").encode("utf-8"))
                                doc_id = h.hexdigest()

                                skip = False
                                if chroma_client is not None and getattr(chroma_client, 'collection', None) is not None:
                                    try:
                                        rec = chroma_client.collection.get(ids=[doc_id], include=['ids'])
                                        ids_list = rec.get('ids', [[]])[0] if rec else []
                                        if ids_list:
                                            skip = True
                                    except Exception:
                                        # if check fails, do not skip ingestion
                                        skip = False

                                if not skip:
                                    try:
                                        if is_cve_json:
                                            # ingest without creating a copy; use original path for metadata
                                            ingest_document(content, filename=fname, folder=None, save_copy=False, original_path=path)
                                        else:
                                            ingest_document(content, filename=fname, folder=None)
                                    except Exception:
                                        logger.exception(f"[vector_ingest] Error ingesting {path}")

                        # Wait interruptibly
                        try:
                            stop_evt.wait(max(1, int(hours)) * 60 * 60)
                        except Exception:
                            __import__("time").sleep(60)
                    except Exception:
                        logger.exception("[vector_ingest] Unexpected error in loop")
                        try:
                            stop_evt.wait(60)
                        except Exception:
                            __import__("time").sleep(60)
            finally:
                logger.info("[vector_ingest] Stopping ingest loop")

        # Ensure folder exists (no-op if missing; worker will just skip)
        try:
            __import__("os").makedirs(folder, exist_ok=True)
        except Exception:
            pass

        try:
            threading.Thread(target=vector_ingest_loop, args=(evt, folder, interval_hours), daemon=True).start()
            logger.info("[worker_controller] vector_ingest started via UI")
        except Exception:
            logger.exception("[worker_controller] Failed to start vector_ingest")
            request.app.state.worker_status[name] = False
            return {"message": "Failed to start vector_ingest"}

    request.app.state.worker_status[name] = True
    logger.info(f"Worker {name} enabled via UI.")
    return {"message": f"Worker {name} enabled"}
