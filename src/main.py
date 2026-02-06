"""
@file main.py
@brief Entry point for the Cyberintelligence FastAPI application.

@details This script initializes the FastAPI app, sets up routes for
RSS feed ingestion and news scraping using Scrapy, schedules periodic
tasks such as NLP processing with spaCy, and launches a dynamic spider
from PostgreSQL using asyncpg.
@author naflashDev
"""

import os
from dotenv import load_dotenv
from pathlib import Path
# Always prefer .env.test if present (test isolation)
env_test = Path(__file__).parent.parent / ".env.test"
if env_test.exists():
    load_dotenv(dotenv_path=env_test)
else:
    load_dotenv()

import asyncio
import threading
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from loguru import logger
import multiprocessing
from app.utils.utils import get_connection_service_parameters, create_config_file 
from app.utils.run_services import ensure_infrastructure, shutdown_services

from app.controllers.routes import (
    scrapy_news_controller,
    spacy_controller,
    tiny_postgres_controller,
    llm_controller,
    status_controller,
    worker_controller,
    network_analysis_controller,
    docs_controller,
    coverage_controller
)
from app.controllers.routes.hashed_controller import router as hashed_router
from app.controllers.routes.config_controller import router as config_controller_router
from app.utils.worker_control import load_worker_settings, save_worker_settings
from app.controllers.routes.scrapy_news_controller import (
    recurring_google_alert_scraper,
    background_scraping_feeds,
    background_scraping_news,
    run_dynamic_spider_from_db,
)
from app.controllers.routes.tiny_postgres_controller import (
    background_rss_process_loop,
)
from app.controllers.routes.spacy_controller import (
    background_process_every_24h,
)

from app.controllers.routes.llm_controller import (
    background_cve_and_finetune_loop,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    @brief Handles FastAPI application startup and shutdown events.

    @details On startup, it:
    - Connects to PostgreSQL
    - Starts Google Alerts recurring scraping
    - Starts RSS feed extraction
    - Starts immediate scraping for feeds and news
    - Starts NLP labeling with spaCy every 24 hours
    - Starts dynamic Scrapy spider from PostgreSQL config

    On shutdown, it:
    - Closes the PostgreSQL connection pool
    """

    # --- DB hash tables auto-creation (SQLite) ---
    try:
        from app.models.db import Base, engine
        from app.models.hash_models import MD5Hash, SHA256Hash, SHA512Hash
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"[Startup] Could not auto-create hash tables: {e}")

    # --- cfg_services.ini config file recreation logic ---
    parameters: tuple = (
        'Ubuntu',
        'install-updater-1,install-web-nginx-1,install-app-1,install-db-1,opensearch-dashboards,opensearch'
    )
    file_name: str = 'cfg_services.ini'
    file_content: list[str] = [
        '# Configuration file.\n',
        '# This file contains the parameters for service orchestration.\n',
        '# ONLY one uncommented line is allowed.\n',
        '# The valid line format is: distro_name=valor;dockers_name=valor;use_ollama=valor\n',
        f'distro_name={parameters[0]};dockers_name={parameters[1]};use_ollama=false\n'
    ]

    from app.utils.utils import get_connection_service_parameters, create_config_file
    retorno_otros = get_connection_service_parameters(file_name)
    logger.info(retorno_otros[1])
    error_occurred = False
    if retorno_otros[0] != 0:
        logger.info('Recreating configuration file...')
        retorno_otros = create_config_file(file_name, file_content)
        logger.info(retorno_otros[1])
        # If the file had to be recreated, default values will be used
        if retorno_otros[0] != 0:
            logger.error('Configuration file missing. Execution cannot continue without a configuration file.')
            error_occurred = True
        else:
            # Intentar leer de nuevo tras crear el archivo
            retorno_otros = get_connection_service_parameters(file_name)
            logger.info(retorno_otros[1])
            if retorno_otros[0] == 0:
                parameters = retorno_otros[2]
    else:
        parameters = retorno_otros[2]  # Get parameters read from the config file

    # We will block on heavy startup work so the server only accepts requests
    # after infrastructure initialization completes.
    app.state.ui_initialized = False
    # infra readiness flag (set after ensure_infrastructure completes)
    app.state.infra_ready = False
    app.state.infra_error = None
    # worker status dictionary (keys set when initializing background tasks)
    app.state.worker_status = {}
    # create lock bound to current event loop for initialization
    app.state.ui_init_lock = asyncio.Lock()

    logger.info("Startup: initializing infrastructure and background tasks (blocking until ready)")
    try:
        # Procesar parámetros obtenidos
        infra_params = {}
        if not error_occurred:
            # Si parameters es una tupla o lista, extraer valores
            # Ahora parameters es siempre un dict
            distro_name = parameters.get('distro_name', 'Ubuntu')
            dockers_name = parameters.get('dockers_name', 'install-updater-1,install-web-nginx-1,install-app-1,install-db-1,opensearch-dashboards,opensearch')

            # El parámetro use_ollama solo debe usarse como flag, nunca como nombre de contenedor
            raw_ollama = parameters.get('use_ollama', 'false')
            if isinstance(raw_ollama, bool):
                use_ollama = raw_ollama
            else:
                use_ollama = str(raw_ollama).strip().lower() == 'true'
            # Eliminar accidentalmente 'use_ollama=true' de dockers_name si está presente
            dockers_name = ','.join([c for c in dockers_name.split(',') if not c.strip().startswith('use_ollama')])

            from app.utils.run_services import is_ollama_available, try_install_ollama, ensure_infrastructure
            import psutil
            min_ram_gb = 8
            min_cpu = 2
            if not use_ollama:
                logger.info("El parámetro use_ollama está en false. Ollama no será instalado ni inicializado. Se pasa el parámetro a run_services.")
                ensure_infrastructure((distro_name, dockers_name), use_ollama=False)
            else:
                ram_ok = psutil.virtual_memory().total >= min_ram_gb * 1024**3
                cpu_ok = psutil.cpu_count(logical=False) >= min_cpu
                if ram_ok and cpu_ok:
                    if not is_ollama_available():
                        logger.info("Ollama no está instalado. Intentando instalar...")
                        host_platform = os.name
                        try_install_ollama(host_platform)
                    else:
                        logger.info("Ollama ya está disponible en el sistema.")
                    ensure_infrastructure((distro_name, dockers_name), use_ollama=True)
                else:
                    logger.warning(f"Hardware insuficiente para Ollama: RAM >= {min_ram_gb}GB, CPU >= {min_cpu} cores requerido. Se pasa el parámetro a run_services.")
                    ensure_infrastructure((distro_name, dockers_name), use_ollama=False)

            try:
                app.state.stop_event = threading.Event()
                app.state.worker_stop_events = {}
                app.state.worker_timers = {}
                app.state.infra_ready = True
            except Exception as e:
                app.state.infra_error = str(e)
                logger.exception("[Startup] ensure_infrastructure failed")
        else:
            app.state.infra_error = 'Configuration file missing. Startup incomplete.'
    except Exception:
        logger.exception("[Startup] Exception during initialization")
        error_occurred = True

    yield

    # Shutdown: close DB pool if it was created by the UI initializer
    logger.info("[Lifespan] Application shutting down.")
    # Signal background threads to stop
    stop_event = getattr(app.state, "stop_event", None)
    if stop_event is not None:
        try:
            stop_event.set()
            logger.info("Signaled background threads to stop.")
        except Exception:
            logger.exception("Error signaling stop_event")
    # mark workers as stopped (best-effort)
    try:
        ws = getattr(app.state, "worker_status", None)
        if isinstance(ws, dict):
            for k in list(ws.keys()):
                ws[k] = False
            app.state.worker_status = ws
    except Exception:
        logger.exception("Error updating worker_status during shutdown")
    pool = getattr(app.state, "pool", None)
    if pool:
        try:
            await pool.close()
            logger.info("[Shutdown] PostgreSQL pool closed.")
        except Exception:
            logger.exception("[Shutdown] Error closing PostgreSQL pool.")
    # Attempt to gracefully shut down external services (compose stacks, Ollama)
    try:
        project_root = Path(__file__).resolve().parents[3]
        # try to derive distro arg if available from earlier startup
        try:
            distro_arg = parameters[0] if parameters and len(parameters) > 0 else None
        except Exception:
            distro_arg = None
        try:
            containers_arg = parameters[1] if parameters and len(parameters) > 1 else None
        except Exception:
            containers_arg = None
        shutdown_services(
            project_root=project_root,
            stop_ollama=True,
            force_stop_containers=True,
            distro_name=distro_arg,
            containers=containers_arg,
        )
        logger.info("Requested shutdown of external services.")
    except Exception:
        logger.exception("Error invoking shutdown_services during lifespan shutdown")


async def initialize_background_tasks(app: FastAPI):
    """Initialize the services that used to run at startup.

    This function is triggered on the first UI access and will:
    - Ensure infrastructure
    - Create DB pool and store it in `app.state.pool`
    - Start background threads/tasks
    """
    # La infraestructura ya se asegura en lifespan. Aquí solo se inicializan pool y workers.
    file_name: str = 'cfg_services.ini'
    file_content: list[str] = [
        '# Configuration file.\n',
        '# This file contains the parameters for connecting to the opensearch database server.\n',
        '# ONLY one uncommented line is allowed.\n',
        '# The valid line format is:distro_name,dockers_name\n',
    ]

    retorno_otros = get_connection_service_parameters(file_name)
    logger.info(retorno_otros[1])
    if retorno_otros[0] != 0:
        logger.info('Recreating configuration file with defaults...')
        default_parameters: tuple = (
            'Ubuntu',
            'install-updater-1,install-web-nginx-1,install-app-1,install-db-1,opensearch-dashboards,opensearch'
        )
        retorno_otros = create_config_file(file_name, file_content + [f"{default_parameters[0]};{default_parameters[1]}\n"]) 
        logger.info(retorno_otros[1])
        if retorno_otros[0] != 0:
            logger.error('Configuration file missing. Background initialization aborted.')
            return
        parameters = default_parameters
    else:
        parameters = retorno_otros[2]

    loop = asyncio.get_running_loop()
    logger.info("[UI-init] Starting background tasks triggered by UI access...")

    # PostgreSQL connection
    try:
        logger.info("[UI-init] Connecting to PostgreSQL database...")
        pool = await asyncpg.create_pool(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
            host=os.getenv("POSTGRES_HOST"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            min_size=5,
            max_size=20,
        )
        app.state.pool = pool
        logger.info("[UI-init] PostgreSQL connection established.")
    except Exception:
        logger.exception("[UI-init] Failed to connect to PostgreSQL.")
        pool = None

    # Required paths
    google_alerts_path = "./data/google_alert_rss.txt"
    urls_path = "./data/urls_cybersecurity_ot_it.txt"
    input_path = "./outputs/result.json"
    output_path = "./outputs/labels_result.json"

    # Load persisted worker preferences
    settings = load_worker_settings()

    # Google Alerts scraper
    if settings.get("google_alerts", True) and os.path.exists(google_alerts_path):
        app.state.worker_status["google_alerts"] = True
        # create stop event for this worker
        evt = threading.Event()
        app.state.worker_stop_events["google_alerts"] = evt
        # start recurring scraper, pass stop event and register timer
        def _register_timer(t):
            app.state.worker_timers["google_alerts"] = t

        threading.Thread(
            target=scrapy_news_controller.recurring_google_alert_scraper,
            args=(loop, evt, _register_timer),
            daemon=True,
        ).start()
        logger.info("[UI-init] Google Alerts scheduler started.")
    else:
        app.state.worker_status["google_alerts"] = False
        logger.warning("[UI-init] google_alert_rss.txt not found or worker disabled in settings.")

    # RSS feed extraction
    if settings.get("rss_extractor", True) and os.path.exists(urls_path):
        app.state.worker_status["rss_extractor"] = True
        evt = threading.Event()
        app.state.worker_stop_events["rss_extractor"] = evt
        def _register_timer_rss(t):
            app.state.worker_timers["rss_extractor"] = t

        threading.Thread(
            target=tiny_postgres_controller.background_rss_process_loop,
            args=(pool, urls_path, loop, evt, _register_timer_rss),
            daemon=True,
        ).start()
        logger.info("[UI-init] RSS extractor scheduled.")
    else:
        app.state.worker_status["rss_extractor"] = False
        logger.warning("[UI-init] urls_cybersecurity_ot_it.txt not found or worker disabled in settings.")

    # Immediate feed & news scraping
    # Scraping feeds/news
    if settings.get("scraping_feeds", True):
        evt = threading.Event()
        app.state.worker_stop_events["scraping_feeds"] = evt
        def _reg_feed(t):
            app.state.worker_timers["scraping_feeds"] = t

        threading.Thread(
            target=scrapy_news_controller.background_scraping_feeds,
            args=(loop, evt, _reg_feed),
            daemon=True,
        ).start()
        app.state.worker_status["scraping_feeds"] = True
    else:
        app.state.worker_status["scraping_feeds"] = False

    if settings.get("scraping_news", True):
        evt2 = threading.Event()
        app.state.worker_stop_events["scraping_news"] = evt2
        def _reg_news(t):
            app.state.worker_timers["scraping_news"] = t

        threading.Thread(
            target=scrapy_news_controller.background_scraping_news,
            args=(loop, evt2, _reg_news),
            daemon=True,
        ).start()
        app.state.worker_status["scraping_news"] = True
    else:
        app.state.worker_status["scraping_news"] = False

    logger.info("[UI-init] Feed and news scraping launched according to settings.")

    # NLP processing (spaCy)
    # spaCy NLP
    if settings.get("spacy_nlp", True) and os.path.exists(input_path):
        app.state.worker_status["spacy_nlp"] = True
        evt = threading.Event()
        app.state.worker_stop_events["spacy_nlp"] = evt
        def _reg_spacy(t):
            app.state.worker_timers["spacy_nlp"] = t

        threading.Thread(
            target=spacy_controller.background_process_every_24h,
            args=(input_path, output_path, evt, _reg_spacy),
            daemon=True,
        ).start()
        logger.info("[UI-init] spaCy NLP labeling scheduled every 24h.")
    else:
        app.state.worker_status["spacy_nlp"] = False
        logger.warning("[UI-init] result.json not found or worker disabled in settings. NLP not launched.")

    # LLM CVE + dataset updater (every 7 days)
    # LLM updater (already accepts stop_event)
    if settings.get("llm_updater", True):
        evt = threading.Event()
        app.state.worker_stop_events["llm_updater"] = evt
        threading.Thread(
            target=llm_controller.background_cve_and_finetune_loop,
            args=(evt,),
            daemon=True,
        ).start()
        app.state.worker_status["llm_updater"] = True
        logger.info("[UI-init] LLM CVE & dataset 7-day scheduler started.")
    else:
        app.state.worker_status["llm_updater"] = False

    # Dynamic Scrapy spider from DB
    # Dynamic Scrapy spider from DB
    if settings.get("dynamic_spider", True) and pool:
        # create stop event and register spot for process
        evt = threading.Event()
        app.state.worker_stop_events["dynamic_spider"] = evt

        def _register_process(p):
            app.state.worker_timers["dynamic_spider"] = p

        # start dynamic spider loop with stop_event and registration callback
        asyncio.create_task(run_dynamic_spider_from_db(pool, stop_event=evt, register_process=_register_process))
        app.state.worker_status["dynamic_spider"] = True
        logger.info("[UI-init] Dynamic spider from DB started.")
    else:
        app.state.worker_status["dynamic_spider"] = False
        logger.warning("[UI-init] DB-based scraper not started (no DB) or worker disabled in settings.")

    # persist current settings (in case defaults were created)
    save_worker_settings(settings)

    # mark initialized
    app.state.ui_initialized = True


# FastAPI app instance
app = FastAPI(
    title="Cyberintelligence API",
    description="Automated processing of RSS feeds, news scraping, "
                "and named entity recognition",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(scrapy_news_controller.router)
app.include_router(spacy_controller.router)
app.include_router(tiny_postgres_controller.router)
app.include_router(llm_controller.router)
app.include_router(status_controller.router)
app.include_router(worker_controller.router)
app.include_router(network_analysis_controller.router)
app.include_router(docs_controller.router)
app.include_router(config_controller_router)
app.include_router(coverage_controller.router)
app.include_router(hashed_router)

# Serve UI static files (simple single-file UI under app/ui/static)
STATIC_DIR = Path(__file__).resolve().parent / "app" / "ui" / "static"
if STATIC_DIR.exists():
    try:
        # Only log mounting once from the main process to avoid duplicate messages
        if multiprocessing.current_process().name == "MainProcess":
            logger.info(f"Mounting UI static files from {STATIC_DIR}")
    except Exception:
        # Fallback to logging if multiprocessing check fails for any reason
        logger.info(f"Mounting UI static files from {STATIC_DIR}")

    app.mount("/ui", StaticFiles(directory=str(STATIC_DIR)), name="ui")
    # Montar htmlcov para servir recursos estáticos del coverage report
    HTMLCOV_DIR = Path(__file__).resolve().parent.parent / "htmlcov"
    if HTMLCOV_DIR.exists():
        app.mount("/coverage", StaticFiles(directory=str(HTMLCOV_DIR)), name="coverage-static")

    # Montar Docs/images para servir imágenes en README y web
    DOCS_IMAGES_DIR = Path(__file__).resolve().parent.parent / "Docs" / "images"
    if DOCS_IMAGES_DIR.exists():
        app.mount("/Docs/images", StaticFiles(directory=str(DOCS_IMAGES_DIR)), name="docs-images")
        logger.info(f"Mounted Docs/images static files from {DOCS_IMAGES_DIR}")
    else:
        logger.warning(f"Docs/images directory not found at {DOCS_IMAGES_DIR}; images will not be served.")

    @app.get("/", include_in_schema=False)
    async def root_index():
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            # Trigger UI-based initialization on first access (non-blocking)
            if not getattr(app.state, "ui_initialized", False):
                # create lock lazily bound to current event loop
                if getattr(app.state, "ui_init_lock", None) is None:
                    app.state.ui_init_lock = asyncio.Lock()

                async def _init_if_needed():
                    async with app.state.ui_init_lock:
                        if getattr(app.state, "ui_initialized", False):
                            return
                        try:
                            await initialize_background_tasks(app)
                        except Exception:
                            logger.exception("[UI-init] Exception during initialization triggered by UI access")

                # schedule initialization in background so UI loads fast
                asyncio.create_task(_init_if_needed())

            return FileResponse(index_path)
        else:
            return {"error": "index.html not found in UI static directory"}
    
    # Also serve the UI index at /ui and /ui/ so static hosting access triggers init
    @app.get("/ui", include_in_schema=False)
    @app.get("/ui/", include_in_schema=False)
    async def ui_index():
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            if not getattr(app.state, "ui_initialized", False):
                if getattr(app.state, "ui_init_lock", None) is None:
                    app.state.ui_init_lock = asyncio.Lock()

                async def _init_if_needed2():
                    async with app.state.ui_init_lock:
                        if getattr(app.state, "ui_initialized", False):
                            return
                        try:
                            await initialize_background_tasks(app)
                        except Exception:
                            logger.exception("[UI-init] Exception during initialization triggered by UI access")

                asyncio.create_task(_init_if_needed2())
            return FileResponse(index_path)
        else:
            return {"error": "index.html not found in UI static directory"}
else:
    logger.warning(f"UI static directory not found at {STATIC_DIR}; UI will not be served from main.py")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",  # origen de TU UI
        "http://localhost:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Entry point
if __name__ == "__main__":
    """
    @brief Launches the FastAPI app using Uvicorn in development mode.

    @details The server runs locally on http://127.0.0.1:8000 with
    auto-reload enabled for development.
    """
    logger.info("Initializing FastAPI application...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
