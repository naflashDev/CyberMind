"""
@file llm_trainer.py
@author naflashDev
@brief Periodic data-preparation service for the local LLM.
@details This module updates the CVE dataset, rebuilds the dataset used for training/evaluation and can be scheduled every 7 days.
"""
import subprocess
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


def update_cve_repo(stop_event=None) -> None:
    '''
    @brief Update the CVE repository by cloning or pulling the latest data and rebuilding the list.

    Calls the helper to update the CVE repo and build the consolidated list.

    @param stop_event Optional threading.Event to allow cancellation.
    @return None.
    '''
    logger.info("[LLM Trainer] Updating CVE list (clone/pull + build)...")
    update_cve_repo_and_build_list(stop_event=stop_event)
    logger.info("[LLM Trainer] CVE list updated successfully.")


def prepare_dataset() -> None:
    '''
    @brief Build the fine-tuning dataset for the LLM.

    Calls the dataset builder to generate the fine-tuning dataset from CVE and news data.

    @return None.
    '''
    logger.info("[LLM Trainer] Building dataset for LLM...")
    build_finetune_dataset()
    logger.info("[LLM Trainer] Dataset ready at ./Data/finetune_data.jsonl.")


def run_periodic_training(stop_event=None) -> None:
    '''
    @brief Entry point for the 7-day periodic workflow.

    Updates CVE data, builds the dataset, and launches Llama 3 LoRA training with the latest dataset.

    @param stop_event Optional threading.Event to allow cancellation.
    @return None.
    '''
    logger.info("[LLM Trainer] Starting periodic workflow (data update + dataset build + training)...")
    update_cve_repo(stop_event=stop_event)
    prepare_dataset()
    logger.info("[LLM Trainer] Periodic workflow finished.")
