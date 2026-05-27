from __future__ import annotations

import logging

from app.utils.app_paths import log_file_path


def configure_logging() -> None:
    path = log_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.FileHandler(path, encoding="utf-8")],
    )


def current_log_file() -> str:
    return str(log_file_path())
