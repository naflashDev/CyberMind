"""
@file llm_trainer.py
@author naflashDev
@brief Periodic data-preparation service for the local LLM.
@details This module updates the CVE dataset, rebuilds the dataset
         used for training/evaluation and can be scheduled every 7 days.
"""

import subprocess
from loguru import logger
import os

from app.services.llm.finetune_dataset_builder import build_finetune_dataset
from app.services.llm.script_auto import update_cve_repo_and_build_list  # según tu ruta real


def update_cve_repo() -> None:
    logger.info("[LLM Trainer] Updating CVE list (clone/pull + build)...")
    update_cve_repo_and_build_list()
    logger.info("[LLM Trainer] CVE list updated successfully.")


def prepare_dataset() -> None:
    logger.info("[LLM Trainer] Building dataset for LLM...")
    build_finetune_dataset()
    logger.info("[LLM Trainer] Dataset ready at ./Data/finetune_data.jsonl.")


def run_periodic_training() -> None:
    """
    @brief Entry point for the 7-day periodic workflow.
    @details
        - Updates CVE data (clone/pull + cve_list.json).
        - Builds the dataset (CVE + news).
        - Launches Llama 3 LoRA training with the latest dataset.
    """
    logger.info("[LLM Trainer] Starting periodic workflow (data update + dataset build + training)...")
    update_cve_repo()
    prepare_dataset()
    logger.info("[LLM Trainer] Periodic workflow finished.")
