"""Configuration loading for the Stellar One report CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str
    verify_ssl: bool | str = True
    timeout_seconds: int = 30


def load_settings() -> Settings:
    """Load settings from environment variables and an optional .env file."""
    load_dotenv(dotenv_path=Path.cwd() / ".env")

    base_url = os.getenv("STELLAR_BASE_URL", "").strip().rstrip("/")
    api_key = os.getenv("STELLAR_API_KEY", "").strip()
    verify_ssl = _ssl_verification_value()

    if not base_url:
        raise ConfigError("Missing STELLAR_BASE_URL. Add it to .env or the environment.")
    if not api_key:
        raise ConfigError("Missing STELLAR_API_KEY. Add it to .env or the environment.")

    return Settings(base_url=base_url, api_key=api_key, verify_ssl=verify_ssl)


def _ssl_verification_value() -> bool | str:
    """Return requests-compatible TLS verification config."""
    ca_bundle = os.getenv("STELLAR_CA_BUNDLE", "").strip()
    if ca_bundle:
        return ca_bundle

    raw_value = os.getenv("STELLAR_VERIFY_SSL", "true").strip().casefold()
    if raw_value in {"0", "false", "no", "off"}:
        return False
    if raw_value in {"1", "true", "yes", "on"}:
        return True
    raise ConfigError("STELLAR_VERIFY_SSL must be true or false.")
