"""Central configuration, loaded from environment variables / .env file."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
APP_SECRETS = PROJECT_ROOT.parent / ".streamlit" / "secrets.toml"  # Svenska Coach secrets
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_MODELS = {
    "claude": "claude-sonnet-5",
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-4.1-mini",
}


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else default


@lru_cache(maxsize=1)
def app_secrets() -> dict[str, Any]:
    """When run locally inside Svenska Coach, reuse ../.streamlit/secrets.toml
    so the same keys don't have to be copied into .env. Env vars always win."""
    if _env("IGNORE_APP_SECRETS") == "1" or not APP_SECRETS.exists():
        return {}
    try:
        try:
            import tomllib  # Python 3.11+
        except ModuleNotFoundError:  # pragma: no cover
            import tomli as tomllib  # type: ignore
        return tomllib.loads(APP_SECRETS.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).warning("Could not read %s: %s", APP_SECRETS, exc)
        return {}


def _secret(*path: str) -> str:
    node: Any = app_secrets()
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return ""
        node = node[key]
    return str(node).strip() if not isinstance(node, dict) else ""


def _llm_key() -> str:
    provider = _env("LLM_PROVIDER", "claude").lower()
    return _env("LLM_API_KEY") or _secret(provider, "api_key")


def _service_account() -> dict[str, Any] | None:
    raw = _env("GCP_SERVICE_ACCOUNT_JSON")
    if raw:
        return json.loads(raw)
    sa = app_secrets().get("gcp_service_account")
    return dict(sa) if isinstance(sa, dict) else None


@dataclass(frozen=True)
class Settings:
    # LLM
    llm_provider: str = field(default_factory=lambda: _env("LLM_PROVIDER", "claude").lower())
    llm_api_key: str = field(default_factory=_llm_key)
    llm_model_override: str = field(default_factory=lambda: _env("LLM_MODEL"))

    # TTS
    tts_provider: str = field(default_factory=lambda: _env("TTS_PROVIDER", "azure").lower())
    tts_api_key: str = field(default_factory=lambda: _env("TTS_API_KEY"))
    azure_region: str = field(default_factory=lambda: _env("AZURE_SPEECH_REGION", "swedencentral"))
    # narrator = podcast host, male = 1st dialogue character, female = 2nd dialogue character
    azure_voice_narrator: str = field(default_factory=lambda: _env("AZURE_VOICE_NARRATOR", "sv-SE-SofieNeural"))
    azure_voice_male: str = field(default_factory=lambda: _env("AZURE_VOICE_MALE", "sv-SE-MattiasNeural"))
    azure_voice_female: str = field(default_factory=lambda: _env("AZURE_VOICE_FEMALE", "sv-SE-HilleviNeural"))
    eleven_voice_narrator: str = field(default_factory=lambda: _env("ELEVENLABS_VOICE_NARRATOR"))
    eleven_voice_male: str = field(default_factory=lambda: _env("ELEVENLABS_VOICE_MALE"))
    eleven_voice_female: str = field(default_factory=lambda: _env("ELEVENLABS_VOICE_FEMALE"))
    eleven_model: str = field(default_factory=lambda: _env("ELEVENLABS_MODEL", "eleven_multilingual_v2"))
    speaking_rate: float = field(default_factory=lambda: float(_env("SPEAKING_RATE", "0.95") or 0.95))

    # Lesson
    target_level: str = field(default_factory=lambda: _env("TARGET_LEVEL", "A2-B1"))
    topic_mode: str = field(default_factory=lambda: _env("TOPIC_MODE", "weekday").lower())
    timezone: str = field(default_factory=lambda: _env("TIMEZONE", "Europe/Stockholm"))

    # Google Drive
    gdrive_client_id: str = field(
        default_factory=lambda: _env("GDRIVE_CLIENT_ID") or _secret("gdrive_oauth", "client_id"))
    gdrive_client_secret: str = field(
        default_factory=lambda: _env("GDRIVE_CLIENT_SECRET") or _secret("gdrive_oauth", "client_secret"))
    gdrive_refresh_token: str = field(
        default_factory=lambda: _env("GDRIVE_REFRESH_TOKEN") or _secret("gdrive_oauth", "refresh_token"))

    # Google Sheets (Svenska Coach's "Ali Svenska Journal")
    sheet_id: str = field(default_factory=lambda: _env("SVENSKA_SHEET_ID") or _secret("svenska_sheet_id"))
    service_account: dict | None = field(default_factory=_service_account, repr=False)
    add_vocab_to_ordbank: bool = field(
        default_factory=lambda: _env("ADD_VOCAB_TO_ORDBANK", "1") not in ("0", "false", "no"))
    gdrive_folder_name: str = field(default_factory=lambda: _env("GDRIVE_FOLDER_NAME", "Svenska Daily Lessons"))

    # Paths / misc
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / _env("DATA_DIR", "data"))
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO").upper())

    @property
    def llm_model(self) -> str:
        return self.llm_model_override or DEFAULT_MODELS.get(self.llm_provider, "")

    @property
    def curriculum_path(self) -> Path:
        return PROJECT_ROOT / "curriculum.json"

    @property
    def state_path(self) -> Path:
        return self.data_dir / "state.json"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "lessons.db"

    @property
    def lessons_dir(self) -> Path:
        return self.data_dir / "lessons"

    @property
    def audio_dir(self) -> Path:
        return self.data_dir / "audio"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"

    @property
    def sheets_enabled(self) -> bool:
        return bool(self.sheet_id and self.service_account)

    @property
    def gdrive_enabled(self) -> bool:
        return all([self.gdrive_client_id, self.gdrive_client_secret, self.gdrive_refresh_token])


def get_settings() -> Settings:
    return Settings()


def setup_logging(level: str = "INFO") -> None:
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    handlers.append(logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8"))
    logging.basicConfig(level=getattr(logging, level, logging.INFO), format=fmt, handlers=handlers, force=True)
