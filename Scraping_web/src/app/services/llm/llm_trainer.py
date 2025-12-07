"""
@file llm_trainer.py
@author naflashDev
@brief Periodic data-preparation service for the local LLM.
@details This module updates the CVE dataset, rebuilds the dataset
         used for training/evaluation and can be scheduled every 7 days.
"""

import subprocess
from loguru import logger
from app.services.llm.finetune_dataset_builder import build_finetune_dataset
from app.services.llm.script_auto import update_cve_repo_and_build_list

def update_cve_repo() -> None:
    """
    @brief Updates the CVE repository and consolidated JSON using script_auto functions.
    @details
        - Clones or pulls the cvelistV5 repository.
        - Rebuilds ./Data/cve_list.json with rich CVE records.
    """
    try:
        logger.info("[LLM Trainer] Updating CVE list with script_auto (clone/pull + build)...")
        update_cve_repo_and_build_list()
        logger.info("[LLM Trainer] CVE list updated successfully.")
    except Exception as e:
        logger.error(f"[LLM Trainer] Error while updating CVE list: {e}")

def prepare_dataset() -> None:
    """
    @brief Rebuilds the dataset for training/evaluation.
    @details Reads:
        - ./Data/cve_list.json
        - ./outputs/result.json
        - ./outputs/labels_result.json
        and generates:
        - ./Data/finetune_data.jsonl
    """
    logger.info("[LLM Trainer] Building dataset for LLM...")
    build_finetune_dataset()
    logger.info("[LLM Trainer] Dataset ready at ./Data/finetune_data.jsonl.")


def run_periodic_training() -> None:
    """
    @brief Entry point for the 7-day periodic workflow.
    @details
        - Updates CVE data.
        - Builds the dataset (CVE + news + labels).
        - (Placeholder) At this stage we only prepare data for the local LLM.
          If in the future you add a remote fine-tuning step, it can be called here.
    """
    logger.info("[LLM Trainer] Starting periodic workflow (data update + dataset build)...")
    update_cve_repo()
    prepare_dataset()
    logger.info("[LLM Trainer] Periodic workflow finished.")
