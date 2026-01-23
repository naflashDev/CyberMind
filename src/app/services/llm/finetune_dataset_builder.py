"""
@file finetune_dataset_builder.py
@author naflashDev
@brief Utilities to build a dataset for LLM training or evaluation.
@details This module reads CVE data and news data and consolidates them
         into an instruction-style JSONL file that can be used for
         fine-tuning pipelines, RAG or evaluation.
"""

import json
import os
from pathlib import Path
from loguru import logger


def _load_json(path: str):
    '''
    @brief Loads a JSON file if it exists.

    Loads a JSON file from the given path if it exists, otherwise returns None.

    @param path File path (str).
    @return Parsed JSON object or None.
    '''
    if not os.path.exists(path):
        logger.warning(f"[FinetuneBuilder] File not found: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[FinetuneBuilder] Error loading {path}: {e}")
        return None


def build_finetune_dataset(
    cve_path: str = "./data/cve_list.json",
    news_path: str = "./outputs/result.json",
    output_path: str = "./outputs/finetune_data.jsonl",
) -> None:
    '''
    @brief Builds a JSONL dataset mixing CVE and news examples.

    Reads CVE and news data, consolidates them into an instruction-style JSONL file for fine-tuning or evaluation.

    @param cve_path Path to consolidated CVE json file (str).
    @param news_path Path to scraped news json file (str).
    @param output_path Output JSONL path for the dataset (str).
    @return None.
    '''
    logger.info("[FinetuneBuilder] Building dataset (CVE + news)...")

    cve_data = _load_json(cve_path) or []
    news_data = _load_json(news_path) or {}

    # Ensure parent directory exists.
    Path(os.path.dirname(output_path) or ".").mkdir(parents=True, exist_ok=True)

    total_examples = 0

    with open(output_path, "w", encoding="utf-8") as fout:
        # -----------------------------------------------------------------
        # CVE examples: script_auto.py ya crea instruction/input/output.
        # -----------------------------------------------------------------
        if isinstance(cve_data, list):
            for item in cve_data:
                try:
                    record = {
                        "instruction": item.get("instruction", ""),
                        "input": item.get("input", ""),
                        "output": item.get("output", ""),
                        "source": "cve",
                    }
                    fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                    total_examples += 1
                except Exception as e:
                    logger.error(f"[FinetuneBuilder] Error processing CVE item: {e}")

        # -----------------------------------------------------------------
        # News examples: simple summarization / explicación.
        # news_data en tu result.json suele ser un dict con 'title' y 'p'.
        # -----------------------------------------------------------------
        if isinstance(news_data, dict):
            title = news_data.get("title", "")
            paragraphs = news_data.get("p", [])
            if isinstance(paragraphs, list):
                body = "\n".join(paragraphs)
            else:
                body = str(paragraphs)

            if body.strip():
                instruction = (
                    "Resume en tres frases en español la siguiente noticia de ciberseguridad."
                )
                input_text = f"Título: {title}\n\nContenido:\n{body}"
                # Placeholder de output: puedes reemplazarlo por resúmenes generados
                # y validados manualmente si lo deseas.
                output_text = (
                    "Resumen no disponible en esta versión del pipeline. "
                    "Este campo puede ser completado con resúmenes generados previamente."
                )

                record = {
                    "instruction": instruction,
                    "input": input_text,
                    "output": output_text,
                    "source": "news",
                }
                fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_examples += 1

    logger.info(
        f"[FinetuneBuilder] Dataset built at {output_path} with {total_examples} examples."
    )
