from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from pathlib import Path

from moviepy.editor import AudioFileClip


@dataclass(frozen=True)
class SubtitleCue:
    index: int
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class SubtitleFile:
    path: Path
    cues: list[SubtitleCue]
    duration: float


class SubtitleGenerator:
    def generate(self, script: str, audio_path: Path, output_path: Path) -> SubtitleFile:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        duration = self._get_audio_duration(audio_path)
        lines = self._split_script(script)
        if not lines:
            raise RuntimeError("Cannot create subtitles from an empty script.")

        cues: list[SubtitleCue] = []

        for index, line in enumerate(lines, start=1):
            start = duration * (index - 1) / len(lines)
            end = duration * index / len(lines)
            if end <= start:
                end = min(duration, start + 0.1)
            cues.append(SubtitleCue(index=index, start=start, end=end, text=line))

        output_path.write_text(self._to_srt(cues), encoding="utf-8")
        return SubtitleFile(path=output_path, cues=cues, duration=duration)

    def _get_audio_duration(self, audio_path: Path) -> float:
        clip = AudioFileClip(str(audio_path))
        try:
            return max(float(clip.duration), 1.0)
        finally:
            clip.close()

    def _split_script(self, script: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", script).strip()
        sentences = re.split(r"(?<=[.!?。！？])\s+", normalized)

        lines: list[str] = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            wrapped = textwrap.wrap(
                sentence,
                width=36,
                break_long_words=False,
                break_on_hyphens=False,
            )
            lines.extend(wrapped or [sentence])

        return lines

    def _to_srt(self, cues: list[SubtitleCue]) -> str:
        blocks = []
        for cue in cues:
            blocks.append(
                "\n".join(
                    [
                        str(cue.index),
                        f"{self._format_time(cue.start)} --> {self._format_time(cue.end)}",
                        cue.text,
                    ]
                )
            )
        return "\n\n".join(blocks) + "\n"

    def _format_time(self, seconds: float) -> str:
        milliseconds = int(round(seconds * 1000))
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, millis = divmod(remainder, 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
