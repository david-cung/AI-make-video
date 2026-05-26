from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts


class VoiceGenerator:
    def __init__(self, voice: str = "vi-VN-HoaiMyNeural", rate: str = "+0%") -> None:
        self.voice = voice
        self.rate = rate

    def generate(self, script: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            asyncio.run(self._generate_async(script, output_path))
        except Exception as exc:
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            raise RuntimeError(
                "Vietnamese voice-over generation failed. "
                "Check your internet connection and edge-tts installation."
            ) from exc

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("Voice generation did not create a valid MP3 file.")
        return output_path

    async def _generate_async(self, script: str, output_path: Path) -> None:
        communicate = edge_tts.Communicate(script, voice=self.voice, rate=self.rate)
        await communicate.save(str(output_path))
