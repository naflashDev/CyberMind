"""
@file worker_control.py
@brief Worker settings persistence and defaults.
@details Provides utilities to read, write and return the default set of
worker boolean settings used by the UI and runtime. The settings are
persisted to `worker_settings.json` in the repository root. Functions:
- `default_settings()` — default worker booleans
- `load_worker_settings()` — read and merge persisted settings
- `save_worker_settings()` — persist settings safely
@date Created: 2025-11-27 12:17:59
@author naflashDev
@project CyberMind
"""

import json
from pathlib import Path
from typing import Dict

SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent / "worker_settings.json"


def default_settings() -> Dict[str, bool]:
    """
    @brief Return the default worker settings mapping.
    @details This function returns a mapping of known worker names to their
    default enabled/disabled boolean values. Callers may use this to ensure
    any persisted settings include all known workers.
    """
    return {
        "google_alerts": False,
        "rss_extractor": False,
        "scraping_feeds": False,
        "scraping_news": False,
        "spacy_nlp": False,
        "llm_updater": False,
        "dynamic_spider": False,
    }


def load_worker_settings() -> Dict[str, bool]:
    """
    @brief Load persisted worker settings from disk.
    @details Reads `worker_settings.json` if present, merges values with
    `default_settings()` to guarantee all known workers are present, and
    returns the resulting dict. On errors or missing file the defaults are
    returned.
    """
    try:
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # ensure all keys exist
            settings = default_settings()
            settings.update({k: bool(v) for k, v in data.items()})
            return settings
    except Exception:
        pass
    return default_settings()


def save_worker_settings(settings: Dict[str, bool]) -> None:
    """
    @brief Persist worker settings to disk.
    @details Writes the provided mapping to `worker_settings.json`. Errors
    while saving are intentionally ignored because the application can
    continue to function with in-memory settings; this keeps the runtime
    resilient when the filesystem is readonly.
    """
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        # ignore persistence errors; not critical
        pass
