from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from app.models.project import ProjectInput
from app.services.script_generator import ScriptGenerator
from app.services.subtitle_generator import SubtitleGenerator
from app.services.templates import get_template
from app.services.video_renderer import VideoRenderer
from app.services.voice_generator import VoiceGenerator
from app.utils.files import make_project_folder


StatusCallback = Callable[[str], None]
ProgressCallback = Callable[[int], None]
ScriptReadyCallback = Callable[[str], None]


@dataclass(frozen=True)
class VideoBuildResult:
    project_folder: Path
    script: str
    script_path: Path
    voice_path: Path
    subtitle_path: Path
    output_video_path: Path
    metadata_path: Path


class VideoBuilder:
    def __init__(
        self,
        script_generator: ScriptGenerator | None = None,
        voice_generator: VoiceGenerator | None = None,
        subtitle_generator: SubtitleGenerator | None = None,
        video_renderer: VideoRenderer | None = None,
    ) -> None:
        self.script_generator = script_generator or ScriptGenerator()
        self.voice_generator = voice_generator or VoiceGenerator()
        self.subtitle_generator = subtitle_generator or SubtitleGenerator()
        self.video_renderer = video_renderer or VideoRenderer()

    def build(
        self,
        project: ProjectInput,
        status: StatusCallback | None = None,
        progress: ProgressCallback | None = None,
        script_ready: ScriptReadyCallback | None = None,
    ) -> VideoBuildResult:
        emit = status or (lambda _message: None)
        emit_progress = progress or (lambda _value: None)
        emit_script = script_ready or (lambda _script: None)

        created_at = datetime.now().astimezone()
        project_folder = make_project_folder(project.output_folder, project.product_name, created_at=created_at)
        template = get_template(project.video_template)
        script_path = project_folder / "script.txt"
        voice_path = project_folder / "voice.mp3"
        subtitle_path = project_folder / "subtitles.srt"
        video_path = project_folder / "output.mp4"
        metadata_path = project_folder / "metadata.json"

        emit("Generating script")
        emit_progress(10)
        script = self.script_generator.generate(project)
        script_path.write_text(script + "\n", encoding="utf-8")
        emit_script(script)
        source = "OpenAI" if self.script_generator.using_openai else "mock fallback"
        emit(f"Script ready ({source}).")
        emit_progress(25)

        emit("Generating voice")
        self.voice_generator.generate(script, voice_path)
        emit(f"Voice-over saved: {voice_path}")
        emit_progress(45)

        emit("Creating subtitles")
        subtitle_file = self.subtitle_generator.generate(script, voice_path, subtitle_path)
        emit(f"Subtitles saved: {subtitle_file.path}")
        emit_progress(60)

        emit("Rendering video")
        self.video_renderer.render(
            background_video_path=project.background_video_path,
            voice_audio_path=voice_path,
            cues=subtitle_file.cues,
            cta_text=project.cta_text,
            output_path=video_path,
        )
        emit_progress(90)

        metadata = {
            "video_template": template.name,
            "template_structure": list(template.structure),
            "product_name": project.product_name,
            "product_benefits": project.product_benefits,
            "target_audience": project.target_audience,
            "video_style": project.video_style,
            "cta_text": project.cta_text,
            "script": script,
            "output_video_path": str(video_path),
            "created_timestamp": created_at.isoformat(timespec="seconds"),
        }
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        return VideoBuildResult(
            project_folder=project_folder,
            script=script,
            script_path=script_path,
            voice_path=voice_path,
            subtitle_path=subtitle_path,
            output_video_path=video_path,
            metadata_path=metadata_path,
        )
