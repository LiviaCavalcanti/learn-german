"""Application settings (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# .../learning/backend/src/sprachheft/config.py -> parents[3] == .../learning
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SPRACHHEFT_",
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Sprachheft"

    # Paths
    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    content_dir: Path = PROJECT_ROOT / "content"

    # Databases
    db_path: Path = PROJECT_ROOT / "data" / "app.sqlite"
    dict_db_path: Path = PROJECT_ROOT / "data" / "dict.sqlite"

    # Dictionary source (WikDict, CC BY-SA 4.0)
    wikdict_base_url: str = "https://download.wikdict.com/dictionaries/sqlite/2"
    dict_pair: str = "de-en"

    # Learner defaults
    default_level: str = "A2"

    # Dev-server network binding (see main.py). Set host to "0.0.0.0" to let other
    # devices on your LAN / Tailscale network (e.g. your phone) connect.
    host: str = "127.0.0.1"
    port: int = 8000

    # LLM — litellm model string, e.g. "ollama/llama3.1", "gpt-4o-mini",
    # "claude-3-5-sonnet-latest". api_base is used for local providers (Ollama).
    llm_model: str = "ollama/llama3.1"
    llm_api_base: str | None = None
    llm_api_key: str | None = None
    llm_temperature: float = 0.3
    # Per-call timeout (seconds). Generation is split into small batches, so each
    # call should finish well within this; it guards against a stuck request.
    llm_timeout: int = 300

    # Embeddings for semantic vocab search (empty = local hashing fallback)
    embedding_model: str = ""

    # CORS — the Vite dev server
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
    # Reflect any Origin. Needed when the frontend is opened from a phone via a
    # LAN / Tailscale IP whose origin isn't known ahead of time.
    cors_allow_all: bool = False

    # Reminders (local HH:MM)
    reminder_time: str = "18:00"
    enable_reminders: bool = True

    # Transcription (optional 'transcribe' extra: yt-dlp + faster-whisper + ffmpeg)
    enable_transcription: bool = True
    whisper_model: str = "base"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
