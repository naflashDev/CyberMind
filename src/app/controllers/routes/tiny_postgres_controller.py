"""
@file tiny_postgres_controller.py
@author naflashDev
@brief FastAPI router for managing RSS feed metadata in PostgreSQL.
@details Provides endpoints to insert, retrieve, and periodically update RSS feed metadata in a PostgreSQL database. Supports background scraping and efficient async queries.
"""

import asyncio
import asyncpg
import os
import threading
import time
from fastapi import APIRouter, Request, HTTPException
from app.services.scraping.spider_rss import extract_rss_and_save
from fastapi import APIRouter, Request, HTTPException, Query
from typing import List
from loguru import logger

from app.models.ttrss_postgre_db import (
    FeedResponse,
    get_feeds_from_db,
)

# Router configuration
router = APIRouter(
    prefix="/postgre-ttrss",
    tags=["Postgre ttrss"],
    responses={
        404: {"description": "Not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        500: {"description": "Internal Server Error"},
    },
)


@router.get("/search-and-insert-rss")
async def search_and_insert_rss(request: Request):
    """
    Starts the background process that runs RSS extraction every 25 hours.

    Args:
        request (Request): Incoming HTTP request object.

    Returns:
        dict: Message confirming that the background process has started.

    Raises:
        HTTPException: If the URL file is not found.
    """
    # ensure database pool is available; try to create one on-demand as fallback
    if not hasattr(request.app.state, 'pool'):
        logger.warning("[RSS] Database pool not initialized in app.state; attempting on-demand creation...")
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
            logger.info("[RSS] Created PostgreSQL pool on-demand.")
        except Exception:
            logger.exception("[RSS] Failed to create PostgreSQL pool on-demand")
            raise HTTPException(status_code=503, detail="Database pool not initialized and on-demand creation failed")
    else:
        pool = request.app.state.pool
    file_path = "./data/urls_cybersecurity_ot_it.txt"

    if not os.path.exists(file_path):
        logger.warning("[Startup] URL file not found. Aborting scheduler.")
        raise HTTPException(status_code=404, detail="URL file not found")


    loop = asyncio.get_running_loop()

    # ensure app.state dicts exist and create stop_event/register so status is tracked
    if getattr(request.app.state, "worker_stop_events", None) is None:
        request.app.state.worker_stop_events = {}
    if getattr(request.app.state, "worker_timers", None) is None:
        request.app.state.worker_timers = {}
    if getattr(request.app.state, "worker_status", None) is None:
        request.app.state.worker_status = {}

    evt = request.app.state.worker_stop_events.get("rss_extractor")
    if evt is None:
        evt = threading.Event()
        request.app.state.worker_stop_events["rss_extractor"] = evt

    def _register_timer(t):
        request.app.state.worker_timers["rss_extractor"] = t

    threading.Thread(
        target=background_rss_process_loop,
        args=(pool, file_path, loop, evt, _register_timer),
        daemon=True
    ).start()

    request.app.state.worker_status["rss_extractor"] = True

    logger.info("[Scheduler] Recurring RSS extraction task initialized.")
    # return only message; UI should query /status for worker list
    return {"message": "Background process started. It will run every 25 hours."}

def background_rss_process_loop(pool, file_path: str, loop: asyncio.AbstractEventLoop, stop_event=None, register_timer=None) -> None:
    """
    Execute the RSS extraction task and reschedule the next execution
    without blocking the main thread.

    This function is intended to be started once in a separate daemon thread.
    It schedules the asynchronous `extract_rss_and_save()` coroutine on the
    provided event loop in a thread-safe manner, then uses a Timer to
    schedule itself again after 25 hours (90000 seconds).

    Args:
        pool: PostgreSQL connection pool.
        file_path (str): Path to the file containing URLs to process.
        loop (asyncio.AbstractEventLoop): Main asyncio event loop.
    """

    async def run_task():
        try:
            logger.info("[RSS] Starting RSS feed extraction and saving...")
            await extract_rss_and_save(pool, file_path)
            logger.success("[RSS] RSS feed extraction and saving completed.")
        except Exception as e:
            logger.error(f"[RSS] Error during RSS extraction and saving: {e}")

    # Schedule the async task on the given event loop
    try:
        future = asyncio.run_coroutine_threadsafe(run_task(), loop)
        # Do not block the worker thread waiting for completion; attach a
        # callback to surface errors when the coroutine ends.
        def _on_done_rss(fut):
            try:
                exc = fut.exception()
                if exc:
                    logger.error(f"[RSS] extract_rss_and_save raised: {exc}")
                else:
                    logger.success("[RSS] RSS feed extraction and saving completed.")
            except Exception as _e:
                logger.error(f"[RSS] Error inspecting future: {_e}")

        try:
            future.add_done_callback(_on_done_rss)
        except Exception:
            logger.debug("Could not attach callback to future; continuing without blocking.")
    except Exception as e:
        logger.error(f"[RSS] Error scheduling RSS extraction task: {e}")

    # Reschedule this function to run again in 25 hours using a Timer if not stopped
    try:
        if stop_event is None or not stop_event.is_set():
            timer = threading.Timer(90000, background_rss_process_loop, args=(pool, file_path, loop, stop_event, register_timer))
            timer.daemon = True
            if callable(register_timer):
                try:
                    register_timer(timer)
                except Exception:
                    pass
            timer.start()
            logger.info("[Scheduler] Next RSS extraction scheduled in 25 hours.")
        else:
            logger.info("[RSS] stop_event set; not scheduling next RSS extraction.")
    except Exception as e:
        logger.error(f"[Scheduler] Error rescheduling RSS extraction: {e}")


@router.get("/feeds", response_model=List[FeedResponse])
async def list_feeds(
    request: Request,
    limit: int = Query(10, ge=1, le=100)
) -> List[FeedResponse]:
    """
    Retrieve a list of RSS feeds from the PostgreSQL database.

    This endpoint retrieves up to a specified number of RSS feeds from the
    PostgreSQL database. The maximum number of feeds returned can be controlled
    via the `limit` query parameter.

    Args:
        request (Request): Incoming HTTP request object.
        limit (int): The number of feed records to return (default is 10).

    Returns:
        List[FeedResponse]: A list of RSS feed metadata in JSON format.
    """
    logger.info("Fetching up to {} feeds from database.", limit)

    try:
        # Ensure pool exists (try on-demand creation as fallback)
        if not hasattr(request.app.state, 'pool'):
            logger.warning("[Feeds] Database pool not initialized in app.state; attempting on-demand creation...")
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
                logger.info("[Feeds] Created PostgreSQL pool on-demand.")
            except Exception:
                logger.exception("[Feeds] Failed to create PostgreSQL pool on-demand")
                raise HTTPException(status_code=503, detail="Database pool not initialized and on-demand creation failed")
        async with request.app.state.pool.acquire() as conn:
            feeds = await get_feeds_from_db(conn, limit)
            logger.success("Successfully fetched {} feeds.", len(feeds))
            return feeds
    except Exception as e:
        logger.error("Error fetching feeds: {}", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving feeds: {str(e)}"
        )




