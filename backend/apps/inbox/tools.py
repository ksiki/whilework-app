import json
import logging
import re
from pathlib import Path

from django.conf import settings

from apps.vacancies.schemas import (
    ContactPlatformEnum,
    ContactSchema,
)

logger = logging.getLogger(__name__)

_SKILL_ALIASES_CACHE: dict | None = None


def _get_skill_aliases() -> dict:
    global _SKILL_ALIASES_CACHE

    if _SKILL_ALIASES_CACHE is not None:
        return _SKILL_ALIASES_CACHE

    file_path = Path(settings.BASE_DIR) / "data" / "skill_aliases.json"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            _SKILL_ALIASES_CACHE = json.load(f)
            logger.info("JSON uploaded successfully")
    except FileNotFoundError:
        logger.warning(
            f"The {file_path} file was not found. Normalization works without a dictionary."
        )
        _SKILL_ALIASES_CACHE = {}
    except json.JSONDecodeError as e:
        logger.error(f"JSON validation error in {file_path}: {e}")
        _SKILL_ALIASES_CACHE = {}

    return _SKILL_ALIASES_CACHE


def normalize_skill_name(skill: str) -> str | None:
    skill = skill.lower().strip()
    skill = re.sub(r"\s+", " ", skill)
    skill = re.sub(r"[^a-zа-я0-9\.\/\-\#\+ ]", "", skill)

    test_key = skill.replace("-", " ")
    aliases_dict = _get_skill_aliases()

    try:
        return aliases_dict[test_key]
    except Exception:
        return skill if len(skill) > 1 else None


def _normalize_telegram(details: str) -> str:
    """Приводит ссылки t.me к формату @username, игнорируя приватные инвайты."""
    text = details.strip()

    match = re.search(r"(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)", text, re.IGNORECASE)
    if match:
        username = match.group(1)
        if username.lower() != "joinchat":
            return f"@{username}"
        return text

    if "t.me/+" in text:
        return text

    if text.startswith("@"):
        return text

    if re.match(r"^[a-zA-Z0-9_]{5,}$", text):
        return f"@{text}"

    return text


def _is_valid_form(details: str) -> bool:
    text = details.lower().strip()
    valid_domains = [
        "docs.google.com/forms",
        "forms.gle",
        "forms.yandex.ru",
        "forms.yandex.com",
    ]
    return any(domain in text for domain in valid_domains)


def process_and_filter_contacts(
    raw_contacts: list[ContactSchema],
) -> list[ContactSchema]:
    valid_contacts = []
    seen = set()

    for contact in raw_contacts:
        platform = contact.platform
        details = contact.details.strip()

        if not details:
            continue

        is_valid = False

        if platform == ContactPlatformEnum.TELEGRAM:
            details = _normalize_telegram(details)
            if details.startswith("@"):
                is_valid = True
            else:
                is_valid = False

        elif platform == ContactPlatformEnum.FORM:
            if _is_valid_form(details):
                is_valid = True

        elif platform == ContactPlatformEnum.EMAIL:
            if "@" in details and "." in details.split("@")[-1]:
                details = details.replace("mailto:", "").strip()
                is_valid = True

        elif platform == ContactPlatformEnum.NUMBER:
            digits_only = re.sub(r"\D", "", details)
            if len(digits_only) >= 8:
                is_valid = True
            else:
                is_valid = False

        if is_valid:
            identifier = f"{platform}_{details.lower()}"
            if identifier not in seen:
                seen.add(identifier)
                valid_contacts.append(ContactSchema(platform=platform, details=details))

    return valid_contacts
