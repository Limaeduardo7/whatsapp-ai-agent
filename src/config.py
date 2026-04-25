from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _env_list(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    evolution_base_url: str = os.getenv("EVOLUTION_BASE_URL", "https://your-evolution-api.com").rstrip("/")
    evolution_instance: str = os.getenv("EVOLUTION_INSTANCE", "default")
    evolution_api_key: str = os.getenv("EVOLUTION_API_KEY", "")
    evolution_webhook_secret: str = os.getenv("EVOLUTION_WEBHOOK_SECRET", "")

    llm_api_url: str = os.getenv("LLM_API_URL", "http://localhost:18789/v1/chat/completions")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model_id: str = os.getenv("LLM_MODEL_ID", "nvidia-kimi/moonshotai/kimi-k2.5")
    thinking_level: str = os.getenv("THINKING_LEVEL", "high")

    gemini_api_key: str = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
    gemini_stt_model: str = os.getenv("GEMINI_STT_MODEL", "gemini-1.5-flash")

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_ids: list[str] = field(default_factory=lambda: _env_list("TELEGRAM_CHAT_IDS"))

    agents_dir: str = os.getenv("AGENTS_DIR", "/root/.openclaw/agents")
    workspace_dir: str = os.getenv("WORKSPACE_DIR", "/root/clawd")
    clients_dir: str = os.getenv("CLIENTS_DIR", "/root/clawd/clients")

    memory_file: str = os.getenv("MEMORY_FILE", "./data/chat_memory.json")
    blacklist_file: str = os.getenv("BLACKLIST_FILE", "./data/ignored_numbers.json")
    db_path: str = os.getenv("DB_PATH", "./data/agent.db")
    log_file: str = os.getenv("LOG_FILE", "./logs/app.log")

    marketing_automation_enabled: bool = _env_bool("MARKETING_AUTOMATION_ENABLED", True)
    ai_agent_enabled: bool = _env_bool("AI_AGENT_ENABLED", True)
    closer_enabled: bool = _env_bool("CLOSER_ENABLED", True)
    typing_enabled: bool = _env_bool("TYPING_ENABLED", True)
    max_history_messages: int = _env_int("MAX_HISTORY_MESSAGES", 12)

    admin_api_key: str = os.getenv("ADMIN_API_KEY", "")
    cors_origins: list[str] = field(default_factory=lambda: _env_list("CORS_ORIGINS") or ["*"])

    hotmart_webhook_secret: str = os.getenv("HOTMART_WEBHOOK_SECRET", "")
    sequences_file: str = os.getenv("SEQUENCES_FILE", "./data/automation_sequences.json")
    scheduler_interval_seconds: int = _env_int("SCHEDULER_INTERVAL_SECONDS", 30)
    hotmart_client_id: str = os.getenv("HOTMART_CLIENT_ID", "")
    hotmart_client_secret: str = os.getenv("HOTMART_CLIENT_SECRET", "")
    hotmart_basic_token: str = os.getenv("HOTMART_BASIC_TOKEN", "").replace("Basic ", "").strip()
    hotmart_auth_url: str = os.getenv("HOTMART_AUTH_URL", "https://api-sec-vlc.hotmart.com/security/oauth/token")
    hotmart_api_base: str = os.getenv("HOTMART_API_BASE", "https://developers.hotmart.com/payments/api/v1")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
