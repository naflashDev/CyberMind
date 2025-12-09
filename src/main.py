"""
@file main.py
@brief Entry point for the Cyberintelligence FastAPI application.

@details This script initializes the FastAPI app, sets up routes for
RSS feed ingestion and news scraping using Scrapy, schedules periodic
tasks such as NLP processing with spaCy, and launches a dynamic spider
from PostgreSQL using asyncpg.

@date Created: 2025-05-05 12:17:59
@author RootAnto
@project Cebolla
"""

import os
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
from app.utils.utils import get_connection_service_parameters, create_config_file 
from app.utils.run_services import ensure_infrastructure

from app.controllers.routes import (
    scrapy_news_controller,
    spacy_controller,
    tiny_postgres_controller,
    llm_controller,
)
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

    # We will defer heavy startup work until the UI is first accessed.
    # Initialize flags used by the UI-triggered initializer.
    app.state.ui_initialized = False
    app.state.ui_init_lock = None

    yield

    # Shutdown: close DB pool if it was created by the UI initializer
    logger.info("[Lifespan] Application shutting down.")
    pool = getattr(app.state, "pool", None)
    if pool:
        try:
            await pool.close()
            logger.info("[Shutdown] PostgreSQL pool closed.")
        except Exception:
            logger.exception("[Shutdown] Error closing PostgreSQL pool.")


async def initialize_background_tasks(app: FastAPI):
    """Initialize the services that used to run at startup.

    This function is triggered on the first UI access and will:
    - Ensure infrastructure
    - Create DB pool and store it in `app.state.pool`
    - Start background threads/tasks
    """
    # Ensure infrastructure is running
    parameters: tuple = (
        'Ubuntu',
        'install_updater_1,install_web-nginx_1,install_app_1,install_db_1,opensearch-dashboards,opensearch'
    )
    file_name: str = 'cfg_services.ini'
    file_content: list[str] = [
        '# Configuration file.\n',
        '# This file contains the parameters for connecting to the opensearch database server.\n',
        '# ONLY one uncommented line is allowed.\n',
        '# The valid line format is:distro_name,dockers_name\n',
        f'{parameters[0]};{parameters[1]}\n'
    ]

    # Get the connection parameters or assign default ones
    retorno_otros = get_connection_service_parameters(file_name)
    logger.info(retorno_otros[1])

    if retorno_otros[0] != 0:
        logger.info('Recreating configuration file...')
        retorno_otros = create_config_file(file_name, file_content)
        logger.info(retorno_otros[1])
        # If the file had to be recreated, default values will be used

        if retorno_otros[0] != 0:
            logger.error('Configuration file missing. Initialization aborted.')
            return
    else:
        parameters = retorno_otros[2]  # Get parameters read from the config file

    try:
        ensure_infrastructure(parameters)
    except Exception as e:
        logger.error(f"Error while ensuring infrastructure: {e}")

    loop = asyncio.get_running_loop()
    logger.info("[UI-init] Starting background tasks triggered by UI access...")

    # PostgreSQL connection
    try:
        logger.info("[UI-init] Connecting to PostgreSQL database...")
        pool = await asyncpg.create_pool(
            user="postgres",
            password="password123",
            database="postgres",
            host="127.0.0.1",
            port=5432,
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

    # Google Alerts scraper
    if os.path.exists(google_alerts_path):
        threading.Thread(
            args=(loop,),
            daemon=True,
        ).start()
        logger.info("[UI-init] Google Alerts scheduler started.")
    else:
        logger.warning("[UI-init] google_alert_rss.txt not found.")

    # RSS feed extraction
    if os.path.exists(urls_path):
        threading.Thread(
            target=background_rss_process_loop,
            args=(pool, urls_path, loop),
            daemon=True,
        ).start()
        logger.info("[UI-init] RSS extractor scheduled.")
    else:
        logger.warning("[UI-init] urls_cybersecurity_ot_it.txt not found.")

    # Immediate feed & news scraping
    threading.Thread(
        target=background_scraping_feeds,
        args=(loop,),
        daemon=True,
    ).start()
    threading.Thread(
        target=background_scraping_news,
        args=(loop,),
        daemon=True,
    ).start()
    logger.info("[UI-init] Feed and news scraping launched.")

    # NLP processing (spaCy)
    if os.path.exists(input_path):
        threading.Thread(
            target=background_process_every_24h,
            args=(input_path, output_path),
            daemon=True,
        ).start()
        logger.info("[UI-init] spaCy NLP labeling scheduled every 24h.")
    else:
        logger.warning("[UI-init] result.json not found. NLP not launched.")

    # LLM CVE + dataset updater (every 7 days)
    threading.Thread(
        target=background_cve_and_finetune_loop,
        daemon=True,
    ).start()
    logger.info("[UI-init] LLM CVE & dataset 7-day scheduler started.")

    # Dynamic Scrapy spider from DB
    if pool:
        asyncio.create_task(run_dynamic_spider_from_db(pool))
        logger.info("[UI-init] Dynamic spider from DB started.")
    else:
        logger.warning("[UI-init] DB-based scraper not started (no DB).")

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
# Register route modules
app.include_router(scrapy_news_controller.router)
app.include_router(spacy_controller.router)
app.include_router(tiny_postgres_controller.router)
app.include_router(llm_controller.router)

# Serve UI static files (simple single-file UI under app/ui/static)
STATIC_DIR = Path(__file__).resolve().parent / "app" / "ui" / "static"
if STATIC_DIR.exists():
    logger.info(f"Mounting UI static files from {STATIC_DIR}")
    app.mount("/ui", StaticFiles(directory=str(STATIC_DIR)), name="ui")

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
