"""
@file llm_controller.py
@author naflashDev
@brief FastAPI routes to interact with the remote LLM.
@details Provides HTTP endpoints for programmatic and UI-based queries.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger
from app.services.llm.llm_client import query_llm
from app.services.llm.llm_trainer import run_periodic_training

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

def background_cve_and_finetune_loop() -> None:
    """
    @brief Background loop to update CVE repo and rebuild LLM dataset every 7 days.
    @details
        - Calls run_periodic_training() once per cycle.
        - Sleeps for 7 days (7 * 24 * 60 * 60 seconds) between executions.
    """
    import time
    from loguru import logger

    while True:
        try:
            logger.info("[LLM Trainer] Starting 7-day CVE update + dataset build cycle...")
            run_periodic_training()
            logger.info("[LLM Trainer] 7-day CVE + dataset cycle finished.")
        except Exception as e:
            logger.error(f"[LLM Trainer] Error in 7-day loop: {e}")
        # Sleep 7 days before the next run.
        time.sleep(7 * 24 * 60 * 60)
