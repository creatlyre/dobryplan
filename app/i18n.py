import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from fastapi import Request, Response

DEFAULT_LOCALE = "pl"
SUPPORTED_LOCALES = {"pl", "en"}
BCP47_BY_LOCALE = {"pl": "pl-PL", "en": "en-US"}

_LOCALES_DIR = Path(__file__).resolve().parent / "locales"


def normalize_locale(raw: str | None) -> str:
    if not raw:
        return DEFAULT_LOCALE
    token = raw.strip().lower().replace("_", "-")
    if not token:
        return DEFAULT_LOCALE
    base = token.split("-", 1)[0]
    if base in SUPPORTED_LOCALES:
        return base
    return DEFAULT_LOCALE


@lru_cache(maxsize=8)
def _load_locale(locale: str) -> dict[str, str]:
    locale_file = _LOCALES_DIR / f"{locale}.json"
    if not locale_file.exists():
        return {}
    with locale_file.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def resolve_locale(request: Request) -> str:
    query_lang = request.query_params.get("lang")
    if query_lang:
        return normalize_locale(query_lang)

    cookie_lang = request.cookies.get("locale")
    if cookie_lang:
        return normalize_locale(cookie_lang)

    accept_language = request.headers.get("accept-language", "")
    if accept_language:
        first_token = accept_language.split(",", 1)[0]
        normalized = normalize_locale(first_token)
        if normalized in SUPPORTED_LOCALES:
            return normalized

    return DEFAULT_LOCALE


def to_bcp47(locale: str) -> str:
    normalized = normalize_locale(locale)
    return BCP47_BY_LOCALE.get(normalized, BCP47_BY_LOCALE[DEFAULT_LOCALE])


def translate(key: str, locale: str | None = None, **kwargs: Any) -> str:
    normalized = normalize_locale(locale)
    localized = _load_locale(normalized)
    fallback = _load_locale("en")

    template = localized.get(key) or fallback.get(key) or key
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template


def get_translator(locale: str) -> Callable[[str], str]:
    normalized = normalize_locale(locale)

    def _t(key: str, **kwargs: Any) -> str:
        return translate(key, normalized, **kwargs)

    return _t


def inject_template_i18n(request: Request, context: dict[str, Any]) -> dict[str, Any]:
    locale = resolve_locale(request)
    context["locale"] = locale
    context["locale_bcp47"] = to_bcp47(locale)
    context["t"] = get_translator(locale)
    return context


def set_locale_cookie_if_param(response: Response, request: Request) -> None:
    """
    Set locale cookie if ?lang=xx query param is present and valid.
    
    Called after locale has been resolved and page rendered.
    Sets httpOnly cookie with 365-day expiry and lax sameSite policy.
    """
    lang_param = request.query_params.get("lang")
    if lang_param:
        normalized = normalize_locale(lang_param)
        if normalized in SUPPORTED_LOCALES:
            response.set_cookie(
                "locale",
                normalized,
                httpOnly=True,
                sameSite="lax",
                max_age=31536000,  # 365 days in seconds
            )
