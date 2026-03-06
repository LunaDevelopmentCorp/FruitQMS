"""Internationalization endpoints: language list, user preference, translations."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db
from src.models.auth import User
from src.middleware.auth import get_current_user
from src.services.i18n_service import (
    get_supported_languages,
    is_valid_language,
    normalize_language,
    NAMESPACES,
    t,
    _translations,
)

router = APIRouter()


class LanguagePreference(BaseModel):
    language: str  # e.g. "en", "es", "fr", "pt", "de"


@router.get("/languages")
async def list_languages():
    """Return all supported languages and available namespaces."""
    return {
        "languages": get_supported_languages(),
        "default": "en",
        "namespaces": NAMESPACES,
    }


@router.get("/me/language")
async def get_my_language(
    current_user: User = Depends(get_current_user),
):
    """Get the current user's language preference."""
    return {
        "language": current_user.language or "en",
        "organization_default": (
            current_user.organization.default_language
            if current_user.organization
            else "en"
        ),
    }


@router.patch("/me/language")
async def set_my_language(
    payload: LanguagePreference,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set the current user's preferred language.

    The frontend (React i18next) should call this when the user
    switches language, then reload translations from its local files.
    """
    if not is_valid_language(payload.language):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{payload.language}'. "
            f"Supported: {', '.join(get_supported_languages().keys())}",
        )
    current_user.language = normalize_language(payload.language)
    db.add(current_user)
    await db.commit()
    return {"language": current_user.language, "message": "Language preference updated"}


@router.get("/translations/{namespace}")
async def get_translations(
    namespace: str,
    lang: str = "en",
):
    """
    Get backend translations for a given namespace and language.

    The React frontend handles its own translations via i18next files;
    this endpoint serves backend-originated strings (error messages,
    notification titles, generated content) so the frontend can display
    them in the user's language.
    """
    if namespace not in _translations:
        raise HTTPException(status_code=404, detail=f"Namespace '{namespace}' not found")

    normalized = normalize_language(lang)
    translations = _translations.get(namespace, {}).get(normalized, {})
    if not translations:
        # Fall back to English
        translations = _translations.get(namespace, {}).get("en", {})

    return {"namespace": namespace, "language": normalized, "translations": translations}
