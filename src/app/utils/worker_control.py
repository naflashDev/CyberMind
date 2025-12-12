import json
from pathlib import Path
from typing import Dict

SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent / "worker_settings.json"


def default_settings() -> Dict[str, bool]:
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
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        # ignore persistence errors; not critical
        pass
