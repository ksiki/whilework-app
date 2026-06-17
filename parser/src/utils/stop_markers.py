import json
import logging
from pathlib import Path
from typing import Final

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
ASSETS: Final[Path] = BASE_DIR / "assets"

logger = logging.getLogger(__name__)


def get_markers() -> set[str]:
    try:
        with open(ASSETS / "stop_markers.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        all_phrases = []
        for _, categories in data.items():
            for _, phrases in categories.items():
                all_phrases.extend(phrases)

        return set(all_phrases)
    except (FileNotFoundError, AttributeError, json.JSONDecodeError) as e:
        logger.error(f"Stop markers read error, e:{e}")
        return set()
