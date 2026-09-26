"""Settings and API key resolution."""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

from .errors import ConfigError

# --- TypeSafe (default provider) ---
ENV_VAR = "TYPESAFE_API_KEY"
KEY_FILE = Path("~/.config/typesafe/api_key")
TYPESAFE_BASE_URL = "https://api.typesafe.ai"
TYPESAFE_MODEL = "jev-latest"

# --- OpenJEV (community gateway to the same Jev model, optional) ---
OPENJEV_ENV_VAR = "OPENJEV_API_KEY"
OPENJEV_BASE_URL = "https://api.openjev.sh"
OPENJEV_MODEL = "openjev"
PROVIDER_ENV_VAR = "JEV_PROVIDER"


@dataclass(frozen=True)
class Settings:
    api_key: str | None = None
    model: str = TYPESAFE_MODEL
    timeout: float = 10.0
    cache_size: int = 1024
    base_url: str = TYPESAFE_BASE_URL
    max_retries: int = 3
    provider: str | None = None


_settings = Settings()


def get_settings() -> Settings:
    return _settings


def set_settings(s: Settings) -> None:
    global _settings
    _settings = s


def reset_settings() -> None:
    set_settings(Settings())


def update_settings(**kwargs) -> Settings:
    """Return and store a copy of the current settings with kwargs applied."""
    s = replace(_settings, **kwargs)
    set_settings(s)
    return s


def resolve_api_key(explicit: str | None) -> str:
    """Look up the API key: explicit value, then env var, then key file."""
    if explicit:
        return explicit
    env = os.environ.get(ENV_VAR)
    if env and env.strip():
        return env.strip()
    path = KEY_FILE.expanduser()
    if path.is_file():
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        if lines and lines[0].strip():
            return lines[0].strip()
    raise ConfigError(
        f"TypeSafe API key not found. Set it via configure(api_key=...), "
        f"the {ENV_VAR} environment variable, or {KEY_FILE}."
    )


def _resolve_openjev_key(explicit: str | None) -> str | None:
    """Look up the OpenJEV API key: explicit value, then env var. None if not found."""
    if explicit:
        return explicit
    env = os.environ.get(OPENJEV_ENV_VAR)
    if env and env.strip():
        return env.strip()
    return None


def resolve_provider(settings: Settings) -> tuple[str, str, str]:
    """Return ``(base_url, model, api_key)`` applying the provider selection rule.

    1. Explicit choice wins: ``settings.provider`` or the ``JEV_PROVIDER`` env var.
       ``"openjev"`` → OpenJEV, ``"typesafe"`` → TypeSafe.
    2. If a TypeSafe key is available → TypeSafe (unchanged default).
    3. If only an OpenJEV key is available → OpenJEV.
    """
    provider = settings.provider or os.environ.get(PROVIDER_ENV_VAR)

    if provider == "openjev":
        key = _resolve_openjev_key(settings.api_key)
        if not key:
            raise ConfigError(
                f"OpenJEV selected but no API key found. Set it via "
                f"configure(api_key=...) or the {OPENJEV_ENV_VAR} environment variable."
            )
        return OPENJEV_BASE_URL, OPENJEV_MODEL, key

    if provider == "typesafe":
        return TYPESAFE_BASE_URL, TYPESAFE_MODEL, resolve_api_key(settings.api_key)

    # Auto-detect: TypeSafe first (unchanged default), then OpenJEV.
    try:
        ts_key = resolve_api_key(settings.api_key)
        return TYPESAFE_BASE_URL, TYPESAFE_MODEL, ts_key
    except ConfigError:
        pass

    oj_key = _resolve_openjev_key(settings.api_key)
    if oj_key:
        return OPENJEV_BASE_URL, OPENJEV_MODEL, oj_key

    raise ConfigError(
        f"No API key found. Set a TypeSafe key via configure(api_key=...), "
        f"the {ENV_VAR} environment variable, or {KEY_FILE}; "
        f"or set {OPENJEV_ENV_VAR} to use OpenJEV."
    )
