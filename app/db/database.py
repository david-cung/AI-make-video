from __future__ import annotations

import os
import sys
import sqlite3
from pathlib import Path

from app.models.project import ProjectRecord


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or self._default_db_path()

    def initialize(self) -> None:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            self.db_path = self._fallback_db_path()
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    script TEXT NOT NULL,
                    output_video_path TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()

    def save_project(self, product_name: str, script: str, output_video_path: Path) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO projects (product_name, script, output_video_path)
                VALUES (?, ?, ?)
                """,
                (product_name, script, str(output_video_path)),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def list_recent_projects(self, limit: int = 10) -> list[ProjectRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, product_name, script, output_video_path, created_at
                FROM projects
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            ProjectRecord(
                id=row["id"],
                product_name=row["product_name"],
                script=row["script"],
                output_video_path=Path(row["output_video_path"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _default_db_path(self) -> Path:
        env_path = os.getenv("AIVB_DB_PATH")
        if env_path:
            return Path(env_path).expanduser()

        if sys.platform == "win32":
            app_data = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
            base_path = Path(app_data) if app_data else Path.home() / "AppData" / "Local"
            return base_path / "AI Affiliate Video Builder" / "projects.sqlite3"

        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "AI Affiliate Video Builder" / "projects.sqlite3"

        return Path.home() / ".local" / "share" / "ai-affiliate-video-builder" / "projects.sqlite3"

    def _fallback_db_path(self) -> Path:
        return Path.cwd() / ".aivb_data" / "projects.sqlite3"
