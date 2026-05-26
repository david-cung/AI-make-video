from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.models.project import ProjectInput
from app.services.script_generator import ScriptGenerator
from app.services.subtitle_generator import SubtitleGenerator
from app.services.video_renderer import VideoRenderer
from app.services.voice_generator import VoiceGenerator
from app.utils.files import make_project_folder


StatusCallback = Callable[[str], None]


@dataclass(frozen=True)
class VideoBuildResult:
    script: str
    voice_path: Path
    subtitle_path: Path
    output_video_path: Path


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

    def build(self, project: ProjectInput, status: StatusCallback | None = None) -> VideoBuildResult:
        emit = status or (lambda _message: None)

        project_folder = make_project_folder(project.output_folder, project.product_name)
        voice_path = project_folder / "voiceover.mp3"
        subtitle_path = project_folder / "subtitles.srt"
        video_path = project_folder / "affiliate_video.mp4"

        emit("Generating affiliate script...")
        script = self.script_generator.generate(project)
        source = "OpenAI" if self.script_generator.using_openai else "mock fallback"
        emit(f"Script ready ({source}).")

        emit("Generating Vietnamese voice-over...")
        self.voice_generator.generate(script, voice_path)
        emit(f"Voice-over saved: {voice_path}")

        emit("Generating subtitle timing...")
        subtitle_file = self.subtitle_generator.generate(script, voice_path, subtitle_path)
        emit(f"Subtitles saved: {subtitle_file.path}")

        emit("Rendering vertical MP4 video...")
        self.video_renderer.render(
            background_video_path=project.background_video_path,
            voice_audio_path=voice_path,
            cues=subtitle_file.cues,
            cta_text=project.cta_text,
            output_path=video_path,
        )

        return VideoBuildResult(
            script=script,
            voice_path=voice_path,
            subtitle_path=subtitle_path,
            output_video_path=video_path,
        )
