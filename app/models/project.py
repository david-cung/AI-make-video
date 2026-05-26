from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectInput:
    product_name: str
    product_benefits: str
    target_audience: str
    video_style: str
    cta_text: str
    background_video_path: Path
    output_folder: Path


@dataclass(frozen=True)
class ProjectRecord:
    id: int | None
    product_name: str
    script: str
    output_video_path: Path
    created_at: str
