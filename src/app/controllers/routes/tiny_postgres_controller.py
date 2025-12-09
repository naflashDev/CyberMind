# @ Author: RootAnto
# @ Project: Cebolla
# @ Create Time: 2025-05-05 10:30:50
# @ Description:
# This FastAPI router provides endpoints for managing and retrieving RSS feed
# metadata stored in a PostgreSQL database. It supports:
#
# 1. `GET /search-and-insert-rss`: Initiates a background thread that periodically
#    (every 25 hours) reads a list of URLs from a local file, extracts valid RSS feeds
#    by scraping those URLs asynchronously, and stores the extracted feed metadata
#    (such as feed title, site URL, and other relevant information) in the database.
#    This process runs independently from the main event loop, preventing blocking
#    of the FastAPI server.
#
# 2. `GET /feeds`: Retrieves a list of stored RSS feeds from the PostgreSQL database,
#    supporting a `limit` query parameter to control the number of results returned
#    (default is 10, with limits between 1 and 100).
#
# The module leverages asynchronous database interactions for efficient queries,
# combined with a safe threading approach to perform periodic background scraping
# without affecting the responsiveness of the API server.
#
# This setup is designed to facilitate automated, ongoing collection and organization
# of cybersecurity-related RSS feed sources.
import asyncio
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
    pool = request.app.state.pool
    file_path = "./data/urls_cybersecurity_ot_it.txt"

    if not os.path.exists(file_path):
        logger.warning("[Startup] URL file not found. Aborting scheduler.")
        raise HTTPException(status_code=404, detail="URL file not found")

    loop = asyncio.get_running_loop()

    threading.Thread(
        target=background_rss_process_loop,
        args=(pool, file_path, loop),
        daemon=True
    ).start()

    logger.info("[Scheduler] Recurring RSS extraction task initialized.")
    return {"message": "Background process started. It will run every 25 hours."}

def background_rss_process_loop(pool,file_path: str,loop: asyncio.AbstractEventLoop,) -> None:
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
        # If you do NOT want to block at all, comment out the next line
        future.result()
    except Exception as e:
        logger.error(f"[RSS] Error scheduling RSS extraction task: {e}")

    # Reschedule this function to run again in 25 hours using a Timer
    try:
        timer = threading.Timer(90000, background_rss_process_loop, args=(pool, file_path, loop))
        timer.daemon = True
        timer.start()
        logger.info("[Scheduler] Next RSS extraction scheduled in 25 hours.")
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




