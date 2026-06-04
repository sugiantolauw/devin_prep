"""Central configuration, loaded from environment / .env.

We keep this deliberately small and explicit: a plain dataclass populated from
clearly-named environment variables. `.env` is loaded once via python-dotenv so
the same names work whether you run locally or in Docker.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    # mock | live
    mode: str = "mock"

    # Devin API
    devin_api_key: str = ""
    devin_base_url: str = "https://api.devin.ai/v1"
    devin_max_acu_limit: int = 10

    # GitHub
    github_token: str = ""
    target_repo: str = "your-org/superset"
    trigger_label: str = "devin-fix"
    github_webhook_secret: str = ""

    # Runtime
    db_path: str = "data/sentinel.db"
    poll_interval_seconds: int = 10
    mock_polls_to_finish: int = 3

    @property
    def is_live(self) -> bool:
        return self.mode.lower() == "live"


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    try:
        return int(raw) if raw not in (None, "") else default
    except ValueError:
        return default


@lru_cache
def get_settings() -> Settings:
    load_dotenv(override=False)
    return Settings(
        mode=os.environ.get("SENTINEL_MODE", "mock"),
        devin_api_key=os.environ.get("DEVIN_API_KEY", ""),
        devin_base_url=os.environ.get("DEVIN_BASE_URL", "https://api.devin.ai/v1"),
        devin_max_acu_limit=_int("DEVIN_MAX_ACU_LIMIT", 10),
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        target_repo=os.environ.get("TARGET_REPO", "your-org/superset"),
        trigger_label=os.environ.get("TRIGGER_LABEL", "devin-fix"),
        github_webhook_secret=os.environ.get("GITHUB_WEBHOOK_SECRET", ""),
        db_path=os.environ.get("SENTINEL_DB_PATH", "data/sentinel.db"),
        poll_interval_seconds=_int("POLL_INTERVAL_SECONDS", 10),
        mock_polls_to_finish=_int("MOCK_POLLS_TO_FINISH", 3),
    )
