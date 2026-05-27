from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path


def safe_filename(value: str, fallback: str = "affiliate_video") -> str:
    normalized_value = value.replace("đ", "d").replace("Đ", "D")
    ascii_value = unicodedata.normalize("NFKD", normalized_value).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", ascii_value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned[:80] or fallback


def ensure_folder(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def make_project_folder(output_folder: Path, product_name: str, created_at: datetime | None = None) -> Path:
    timestamp = (created_at or datetime.now()).strftime("%Y%m%d_%H%M%S")
    folder_name = f"{timestamp}_{safe_filename(product_name)}"
    return ensure_folder(output_folder / folder_name)
