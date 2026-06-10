import json
import os
from typing import Any, Dict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSLATIONS_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "translations.json"))

SUPPORTED_LANGUAGES = ("es", "en")
DEFAULT_LANGUAGE = "es"
_current_language = DEFAULT_LANGUAGE
_translations: Dict[str, Dict[str, Any]] = {}


def _load_translations() -> None:
    global _translations
    try:
        with open(TRANSLATIONS_PATH, "r", encoding="utf-8") as handle:
            _translations = json.load(handle)
    except Exception:
        _translations = {}


_load_translations()


def set_language(language: str) -> None:
    global _current_language
    _current_language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def get_language() -> str:
    return _current_language


def t(key: str, default: str = "", **kwargs: Any) -> str:
    if not _translations:
        return default or key

    lang_map = _translations.get(_current_language, {})
    text = lang_map.get(key)
    if text is None:
        text = _translations.get(DEFAULT_LANGUAGE, {}).get(key, default or key)
    if kwargs and isinstance(text, str):
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


def localize_date(dt) -> str:
    if not _translations:
        return dt.strftime("%A, %d %B %Y")

    lang_map = _translations.get(_current_language, {})
    weekdays = lang_map.get("date.weekdays", [])
    months = lang_map.get("date.months", [])
    fmt = lang_map.get("date.format_full", "{weekday}, {day} {month} {year}")
    try:
        weekday = weekdays[dt.weekday()] if weekdays else dt.strftime("%A")
        month = months[dt.month - 1] if months else dt.strftime("%B")
        return fmt.format(weekday=weekday, day=dt.day, month=month, year=dt.year)
    except Exception:
        return dt.strftime("%A, %d %B %Y")
