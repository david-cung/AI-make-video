from __future__ import annotations

import os
import sys
from pathlib import Path


APP_DIR_NAME = "AI Affiliate Video Builder"
APP_SLUG = "ai-affiliate-video-builder"


def app_data_dir() -> Path:
    env_path = os.getenv("AIVB_APP_DATA_DIR")
    preferred_path = Path(env_path).expanduser() if env_path else _platform_app_data_dir()
    return _ensure_writable_dir(preferred_path)


def database_path() -> Path:
    env_path = os.getenv("AIVB_DB_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return app_data_dir() / "projects.sqlite3"


def log_file_path() -> Path:
    env_path = os.getenv("AIVB_LOG_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return app_data_dir() / "logs" / "app.log"


def _platform_app_data_dir() -> Path:
    if sys.platform == "win32":
        app_data = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        base_path = Path(app_data) if app_data else Path.home() / "AppData" / "Local"
        return base_path / APP_DIR_NAME

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME

    return Path.home() / ".local" / "share" / APP_SLUG


def _ensure_writable_dir(path: Path) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".write_test"
        test_file.write_text("", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return path
    except OSError:
        fallback = Path.cwd() / ".aivb_data"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback
