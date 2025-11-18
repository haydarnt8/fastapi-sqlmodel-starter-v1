"""
Internationalization (i18n) Module

Provides multilingual support for the API with Arabic and English languages.

Usage:
    from app.i18n import get_translator, get_language

    # In a route handler
    @router.get("/example")
    async def example(request: Request):
        t = get_translator(request)
        message = t("common.success")
        return {"message": message}
"""

from app.i18n.translator import (
    Translator,
    get_translator,
    get_language,
    load_translations,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
)

__all__ = [
    "Translator",
    "get_translator",
    "get_language",
    "load_translations",
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
]
