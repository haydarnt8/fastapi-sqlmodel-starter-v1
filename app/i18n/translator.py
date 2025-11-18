"""
Translation System

Handles loading and retrieving translations for different languages.
Supports nested keys using dot notation (e.g., "auth.login_success").
"""

import json
from pathlib import Path
from typing import Dict, Optional, Any
from fastapi import Request
from contextvars import ContextVar

from app.core.logging import get_logger

logger = get_logger(__name__)

# Supported languages
SUPPORTED_LANGUAGES = ["en", "ar"]
DEFAULT_LANGUAGE = "en"

# Store translations in memory
_translations: Dict[str, Dict[str, Any]] = {}

# Context variable to store current language per request
_current_language: ContextVar[str] = ContextVar("current_language", default=DEFAULT_LANGUAGE)


def load_translations() -> None:
    """
    Load all translation files from the locales directory.

    This should be called once at application startup.
    """
    global _translations

    locales_dir = Path(__file__).parent / "locales"

    if not locales_dir.exists():
        logger.warning(f"Locales directory not found: {locales_dir}")
        return

    for lang_code in SUPPORTED_LANGUAGES:
        lang_file = locales_dir / f"{lang_code}.json"

        if not lang_file.exists():
            logger.warning(f"Translation file not found: {lang_file}")
            continue

        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                _translations[lang_code] = json.load(f)
            logger.info(f"Loaded translations for: {lang_code}")
        except Exception as e:
            logger.error(f"Failed to load translations for {lang_code}: {e}")


def get_language(request: Request) -> str:
    """
    Get the preferred language from the request.

    Priority:
    1. Query parameter: ?lang=ar
    2. Header: Accept-Language: ar
    3. Default: en

    Args:
        request: FastAPI request object

    Returns:
        Language code (e.g., "en", "ar")
    """
    # Check query parameter
    lang = request.query_params.get("lang")
    if lang and lang in SUPPORTED_LANGUAGES:
        return lang

    # Check Accept-Language header
    accept_lang = request.headers.get("Accept-Language", "")
    for supported in SUPPORTED_LANGUAGES:
        if supported in accept_lang.lower():
            return supported

    # Return default
    return DEFAULT_LANGUAGE


def set_language(lang: str) -> None:
    """
    Set the current language for the current request context.

    Args:
        lang: Language code
    """
    if lang in SUPPORTED_LANGUAGES:
        _current_language.set(lang)
    else:
        logger.warning(f"Unsupported language: {lang}, using default: {DEFAULT_LANGUAGE}")
        _current_language.set(DEFAULT_LANGUAGE)


class Translator:
    """
    Translator class for handling translations.

    Usage:
        t = Translator("ar")
        message = t("auth.login_success")
        formatted = t("validation.min_length", min=8)
    """

    def __init__(self, language: str = DEFAULT_LANGUAGE):
        """
        Initialize translator with a specific language.

        Args:
            language: Language code (e.g., "en", "ar")
        """
        self.language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

    def __call__(self, key: str, **kwargs) -> str:
        """
        Get translation for a key.

        Args:
            key: Translation key in dot notation (e.g., "auth.login_success")
            **kwargs: Variables to format in the translation string

        Returns:
            Translated string
        """
        return self.get(key, **kwargs)

    def get(self, key: str, **kwargs) -> str:
        """
        Get translation for a key.

        Args:
            key: Translation key in dot notation (e.g., "auth.login_success")
            **kwargs: Variables to format in the translation string

        Returns:
            Translated string

        Examples:
            >>> t = Translator("en")
            >>> t.get("auth.login_success")
            "Login successful"
            >>> t.get("validation.min_length", min=8)
            "Minimum length is 8"
        """
        # Get translations for current language
        lang_translations = _translations.get(self.language, {})

        # Navigate nested keys
        keys = key.split(".")
        value = lang_translations

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break

        # If translation not found, try English as fallback
        if value is None and self.language != DEFAULT_LANGUAGE:
            logger.warning(f"Translation not found for key '{key}' in '{self.language}', using fallback")
            fallback_trans = _translations.get(DEFAULT_LANGUAGE, {})
            value = fallback_trans
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = None
                    break

        # If still not found, return the key itself
        if value is None:
            logger.warning(f"Translation not found for key: {key}")
            return key

        # Format with variables if provided
        if kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.error(f"Error formatting translation '{key}': {e}")
                return value

        return value

    def exists(self, key: str) -> bool:
        """
        Check if a translation key exists.

        Args:
            key: Translation key

        Returns:
            True if key exists, False otherwise
        """
        lang_translations = _translations.get(self.language, {})
        keys = key.split(".")
        value = lang_translations

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return False

        return value is not None


def get_translator(request: Request) -> Translator:
    """
    Get translator for the current request.

    Detects language from request and returns appropriate translator.

    Args:
        request: FastAPI request object

    Returns:
        Translator instance

    Usage:
        @router.get("/example")
        async def example(request: Request):
            t = get_translator(request)
            return {"message": t("common.success")}
    """
    lang = get_language(request)
    set_language(lang)
    return Translator(lang)


def translate(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """
    Quick translation function.

    Args:
        key: Translation key
        lang: Language code (optional, uses context variable if not provided)
        **kwargs: Variables for formatting

    Returns:
        Translated string
    """
    if lang is None:
        lang = _current_language.get()

    translator = Translator(lang)
    return translator.get(key, **kwargs)
