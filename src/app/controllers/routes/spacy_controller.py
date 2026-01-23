
"""
@file spacy_controller.py
@author naflashDev
@brief REST API to process a JSON file using entity analysis with spaCy.
@details This endpoint reads a `result.json` file, processes it to extract named entities, and returns a generated `labels_result.json` file.
"""


import os
import threading
from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from app.services.spacy.text_processor import process_json

router = APIRouter(
    tags=["spacy"],
    responses={
        200: {"description": "Processed file returned successfully"},
        404: {"description": "Input file result.json not found"},
        500: {"description": "Failed to generate output file labels_result.json"}
    }
)


@router.get("/start-spacy")
async def start_background_loop(request: Request = None):
    """
    Manually starts the recurring SpaCy processing job every 24 hours in the background.

    Returns:
        dict: Status message confirming that the recurring task has been initiated.

    Raises:
        HTTPException: If the input file `result.json` is not found.
    """
    input_path = "./outputs/result.json"
    output_path = "./outputs/labels_result.json"

    if not os.path.exists(input_path):
        logger.warning("[Startup] Input file result.json not found. Aborting scheduler.")
        raise HTTPException(
            status_code=404,
            detail="File result.json not found"
        )

    # create a stop_event and register timer in app.state if request provided
    if request is not None:
        # ensure app.state dictionaries exist
        if getattr(request.app.state, "worker_stop_events", None) is None:
            request.app.state.worker_stop_events = {}
        if getattr(request.app.state, "worker_timers", None) is None:
            request.app.state.worker_timers = {}
        if getattr(request.app.state, "worker_status", None) is None:
            request.app.state.worker_status = {}

        evt = request.app.state.worker_stop_events.get("spacy_nlp")
        register = None
        if evt is None:
            evt = threading.Event()
            request.app.state.worker_stop_events["spacy_nlp"] = evt
        def _register_timer(t):
            request.app.state.worker_timers["spacy_nlp"] = t
        register = _register_timer

        # mark worker as running in app state so /status reflects it
        request.app.state.worker_status["spacy_nlp"] = True

    threading.Thread(
        target=background_process_every_24h,
        args=(input_path, output_path, evt, register),
        daemon=True
    ).start()

    logger.info("[Scheduler] SpaCy recurring labeling task initialized.")
    # return only message; UI should query /status for worker list
    return {"message": "Background process started. Will re-run every 24 hours."}


def background_process_every_24h(input_path: str, output_path: str, stop_event=None, register_timer=None):
    """
    Executes the JSON NLP processing task and schedules the next execution after 24 hours.

    Args:
        input_path (str): Path to the input JSON file with raw news/texts.
        output_path (str): Path to save the output file with extracted SpaCy labels.
    """
    try:
        logger.info("[SpaCy] Starting entity labeling on result.json...")
        process_json(input_path, output_path)
        logger.success("[SpaCy] Entity labeling completed. Output saved to labels_result.json")
    except Exception as e:
        logger.error(f"[SpaCy] Error while labeling entities: {e}")

    # Schedule next execution in 24 hours if not stopped
    try:
        if stop_event is None or not stop_event.is_set():
            timer = threading.Timer(86400, background_process_every_24h, args=(input_path, output_path, stop_event, register_timer))
            timer.daemon = True
            if callable(register_timer):
                try:
                    register_timer(timer)
                except Exception:
                    pass
            timer.start()
            logger.info("[Scheduler] Next SpaCy entity labeling scheduled in 24 hours.")
        else:
            logger.info("[SpaCy] stop_event set; not scheduling next run.")
    except Exception as e:
        logger.error(f"[Scheduler] Error scheduling next SpaCy run: {e}")
