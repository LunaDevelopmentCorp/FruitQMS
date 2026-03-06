"""
Internationalization (i18n) service for FruitQMS.

Provides language detection, user preference management,
and a translation lookup interface compatible with both
the FastAPI backend and FruitPak's React frontend (i18next).

Supported languages:
  en — English (default)
  es — Español
  fr — Français
  pt — Português
  de — Deutsch
"""

from typing import Optional
from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db

# ---------------------------------------------------------------------------
# Language registry
# ---------------------------------------------------------------------------
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "pt": "Português",
    "de": "Deutsch",
}

DEFAULT_LANGUAGE = "en"

# Translation namespaces — mirrors FruitPak's 14 React i18next namespaces
# plus QMS-specific ones
NAMESPACES = [
    "common",
    "auth",
    "dashboard",
    "forms",
    "intake",
    "process_checks",
    "final_inspection",
    "daily_checklists",
    "growers",
    "packhouses",
    "compliance",
    "reports",
    "settings",
    "validation",
    "errors",
    "notifications",
    "setup_wizard",
]


def get_supported_languages() -> dict[str, str]:
    """Return dict of supported language codes → display names."""
    return SUPPORTED_LANGUAGES.copy()


def is_valid_language(lang_code: str) -> bool:
    """Check if a language code is supported."""
    return lang_code.lower() in SUPPORTED_LANGUAGES


def normalize_language(lang_code: str) -> str:
    """
    Normalize a language code to a supported one.

    Handles variants like 'en-US' → 'en', 'pt-BR' → 'pt'.
    Falls back to DEFAULT_LANGUAGE if not recognized.
    """
    code = lang_code.lower().split("-")[0].split("_")[0]
    if code in SUPPORTED_LANGUAGES:
        return code
    return DEFAULT_LANGUAGE


def detect_language_from_request(request: Request) -> str:
    """
    Detect preferred language from the HTTP Accept-Language header.

    Priority:
    1. X-Language header (explicit override from frontend)
    2. Accept-Language header (browser negotiation)
    3. Default language
    """
    # Check explicit header first (set by React frontend / i18next)
    explicit = request.headers.get("X-Language")
    if explicit and is_valid_language(explicit):
        return normalize_language(explicit)

    # Parse Accept-Language header
    accept_lang = request.headers.get("Accept-Language", "")
    if accept_lang:
        # Simple parser: take the first matching language
        for part in accept_lang.split(","):
            lang = part.split(";")[0].strip()
            normalized = normalize_language(lang)
            if normalized != DEFAULT_LANGUAGE or lang.lower().startswith("en"):
                return normalized

    return DEFAULT_LANGUAGE


async def get_user_language(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> str:
    """
    FastAPI dependency that resolves the current request's language.

    Priority:
    1. X-Language header (per-request override)
    2. Authenticated user's stored preference
    3. Accept-Language header
    4. Organization default
    5. System default ('en')

    Usage in endpoints:
        @router.get("/example")
        async def example(lang: str = Depends(get_user_language)):
            ...
    """
    # 1. Explicit header override
    explicit = request.headers.get("X-Language")
    if explicit and is_valid_language(explicit):
        return normalize_language(explicit)

    # 2. Try to get from authenticated user (non-blocking)
    try:
        from src.middleware.auth import get_current_user
        user = await get_current_user(request, db)
        if user and user.language:
            return normalize_language(user.language)
        # 4. Fall back to org default
        if user and user.organization and user.organization.default_language:
            return normalize_language(user.organization.default_language)
    except Exception:
        pass  # Not authenticated or error — fall through

    # 3. Accept-Language header
    return detect_language_from_request(request)


# ---------------------------------------------------------------------------
# Backend translation store (lightweight — main translations live in React)
# ---------------------------------------------------------------------------
# The backend only needs translations for API error messages, email subjects,
# notification titles, and generated document content. The bulk of the UI
# translations live in the React frontend using i18next files.

_translations: dict[str, dict[str, dict[str, str]]] = {
    # namespace -> lang -> key -> translated string
    "errors": {
        "en": {
            "not_found": "Resource not found",
            "unauthorized": "Authentication required",
            "forbidden": "You do not have permission to access this resource",
            "validation_error": "Validation error",
            "server_error": "Internal server error",
        },
        "es": {
            "not_found": "Recurso no encontrado",
            "unauthorized": "Autenticación requerida",
            "forbidden": "No tiene permiso para acceder a este recurso",
            "validation_error": "Error de validación",
            "server_error": "Error interno del servidor",
        },
        "fr": {
            "not_found": "Ressource non trouvée",
            "unauthorized": "Authentification requise",
            "forbidden": "Vous n'avez pas la permission d'accéder à cette ressource",
            "validation_error": "Erreur de validation",
            "server_error": "Erreur interne du serveur",
        },
        "pt": {
            "not_found": "Recurso não encontrado",
            "unauthorized": "Autenticação necessária",
            "forbidden": "Você não tem permissão para acessar este recurso",
            "validation_error": "Erro de validação",
            "server_error": "Erro interno do servidor",
        },
        "de": {
            "not_found": "Ressource nicht gefunden",
            "unauthorized": "Authentifizierung erforderlich",
            "forbidden": "Sie haben keine Berechtigung auf diese Ressource zuzugreifen",
            "validation_error": "Validierungsfehler",
            "server_error": "Interner Serverfehler",
        },
    },
    "notifications": {
        "en": {
            "inspection_created": "New inspection recorded",
            "non_conformance": "Non-conformance detected",
            "checklist_due": "Daily checklist is due",
            "audit_reminder": "Audit preparation reminder",
        },
        "es": {
            "inspection_created": "Nueva inspección registrada",
            "non_conformance": "No conformidad detectada",
            "checklist_due": "Lista de verificación diaria pendiente",
            "audit_reminder": "Recordatorio de preparación de auditoría",
        },
        "fr": {
            "inspection_created": "Nouvelle inspection enregistrée",
            "non_conformance": "Non-conformité détectée",
            "checklist_due": "Liste de contrôle quotidienne à compléter",
            "audit_reminder": "Rappel de préparation d'audit",
        },
        "pt": {
            "inspection_created": "Nova inspeção registrada",
            "non_conformance": "Não conformidade detectada",
            "checklist_due": "Lista de verificação diária pendente",
            "audit_reminder": "Lembrete de preparação para auditoria",
        },
        "de": {
            "inspection_created": "Neue Inspektion erfasst",
            "non_conformance": "Nichtkonformität festgestellt",
            "checklist_due": "Tägliche Checkliste fällig",
            "audit_reminder": "Erinnerung an Auditvorbereitung",
        },
    },
    "validation": {
        "en": {
            "required_field": "This field is required",
            "invalid_email": "Invalid email address",
            "min_length": "Must be at least {min} characters",
            "max_length": "Must be at most {max} characters",
            "invalid_date": "Invalid date format",
            "out_of_range": "Value must be between {min} and {max}",
            "duplicate_entry": "This entry already exists",
            "invalid_ggn": "Invalid GGN number format",
        },
        "es": {
            "required_field": "Este campo es obligatorio",
            "invalid_email": "Dirección de correo electrónico no válida",
            "min_length": "Debe tener al menos {min} caracteres",
            "max_length": "Debe tener como máximo {max} caracteres",
            "invalid_date": "Formato de fecha no válido",
            "out_of_range": "El valor debe estar entre {min} y {max}",
            "duplicate_entry": "Esta entrada ya existe",
            "invalid_ggn": "Formato de número GGN no válido",
        },
        "fr": {
            "required_field": "Ce champ est obligatoire",
            "invalid_email": "Adresse e-mail invalide",
            "min_length": "Doit contenir au moins {min} caractères",
            "max_length": "Doit contenir au maximum {max} caractères",
            "invalid_date": "Format de date invalide",
            "out_of_range": "La valeur doit être comprise entre {min} et {max}",
            "duplicate_entry": "Cette entrée existe déjà",
            "invalid_ggn": "Format de numéro GGN invalide",
        },
        "pt": {
            "required_field": "Este campo é obrigatório",
            "invalid_email": "Endereço de e-mail inválido",
            "min_length": "Deve ter pelo menos {min} caracteres",
            "max_length": "Deve ter no máximo {max} caracteres",
            "invalid_date": "Formato de data inválido",
            "out_of_range": "O valor deve estar entre {min} e {max}",
            "duplicate_entry": "Esta entrada já existe",
            "invalid_ggn": "Formato de número GGN inválido",
        },
        "de": {
            "required_field": "Dieses Feld ist erforderlich",
            "invalid_email": "Ungültige E-Mail-Adresse",
            "min_length": "Muss mindestens {min} Zeichen lang sein",
            "max_length": "Darf höchstens {max} Zeichen lang sein",
            "invalid_date": "Ungültiges Datumsformat",
            "out_of_range": "Wert muss zwischen {min} und {max} liegen",
            "duplicate_entry": "Dieser Eintrag existiert bereits",
            "invalid_ggn": "Ungültiges GGN-Nummernformat",
        },
    },
    "compliance": {
        "en": {
            "control_point_met": "Control point requirement met",
            "control_point_not_met": "Control point requirement not met",
            "major_must": "Major Must",
            "minor_must": "Minor Must",
            "recommendation": "Recommendation",
            "audit_scheduled": "Audit scheduled",
            "corrective_action_required": "Corrective action required",
            "compliance_score": "Compliance score",
        },
        "es": {
            "control_point_met": "Requisito del punto de control cumplido",
            "control_point_not_met": "Requisito del punto de control no cumplido",
            "major_must": "Obligación Mayor",
            "minor_must": "Obligación Menor",
            "recommendation": "Recomendación",
            "audit_scheduled": "Auditoría programada",
            "corrective_action_required": "Acción correctiva requerida",
            "compliance_score": "Puntuación de cumplimiento",
        },
        "fr": {
            "control_point_met": "Exigence du point de contrôle satisfaite",
            "control_point_not_met": "Exigence du point de contrôle non satisfaite",
            "major_must": "Obligation Majeure",
            "minor_must": "Obligation Mineure",
            "recommendation": "Recommandation",
            "audit_scheduled": "Audit planifié",
            "corrective_action_required": "Action corrective requise",
            "compliance_score": "Score de conformité",
        },
        "pt": {
            "control_point_met": "Requisito do ponto de controlo cumprido",
            "control_point_not_met": "Requisito do ponto de controlo não cumprido",
            "major_must": "Obrigação Maior",
            "minor_must": "Obrigação Menor",
            "recommendation": "Recomendação",
            "audit_scheduled": "Auditoria agendada",
            "corrective_action_required": "Ação corretiva necessária",
            "compliance_score": "Pontuação de conformidade",
        },
        "de": {
            "control_point_met": "Anforderung des Kontrollpunkts erfüllt",
            "control_point_not_met": "Anforderung des Kontrollpunkts nicht erfüllt",
            "major_must": "Hauptanforderung",
            "minor_must": "Nebenanforderung",
            "recommendation": "Empfehlung",
            "audit_scheduled": "Audit geplant",
            "corrective_action_required": "Korrekturmaßnahme erforderlich",
            "compliance_score": "Konformitätsbewertung",
        },
    },
}


def t(namespace: str, key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """
    Translate a key from the backend translation store.

    Usage:
        message = t("errors", "not_found", lang="es")
        # → "Recurso no encontrado"

    Falls back to English if the language or key is missing.
    """
    ns = _translations.get(namespace, {})
    # Try requested language
    lang_dict = ns.get(normalize_language(lang), {})
    if key in lang_dict:
        return lang_dict[key]
    # Fall back to English
    en_dict = ns.get("en", {})
    return en_dict.get(key, key)
