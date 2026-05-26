from __future__ import annotations

import math
import os
import shutil
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# MoviePy 1.0.3 still references Image.ANTIALIAS when Pillow is new enough
# to expose that value only through Image.Resampling.
if not hasattr(Image, "ANTIALIAS") and hasattr(Image, "Resampling"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, VideoFileClip, vfx

from app.services.subtitle_generator import SubtitleCue


class VideoRenderer:
    WIDTH = 1080
    HEIGHT = 1920

    def render(
        self,
        background_video_path: Path,
        voice_audio_path: Path,
        cues: list[SubtitleCue],
        cta_text: str,
        output_path: Path,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._validate_inputs(background_video_path, voice_audio_path)

        background_clip = VideoFileClip(str(background_video_path))
        audio_clip = AudioFileClip(str(voice_audio_path))
        clips_to_close = [background_clip, audio_clip]

        try:
            duration = max(float(audio_clip.duration), 1.0)
            vertical_clip = self._prepare_background(background_clip, duration)
            vertical_clip = vertical_clip.set_audio(audio_clip)
            clips_to_close.append(vertical_clip)

            with tempfile.TemporaryDirectory(prefix="aivb_text_") as temp_dir:
                overlay_clips = self._build_text_overlays(Path(temp_dir), cues, cta_text, duration)
                clips_to_close.extend(overlay_clips)

                final_clip = CompositeVideoClip(
                    [vertical_clip, *overlay_clips],
                    size=(self.WIDTH, self.HEIGHT),
                ).set_duration(duration)
                clips_to_close.append(final_clip)

                final_clip.write_videofile(
                    str(output_path),
                    fps=30,
                    codec="libx264",
                    audio_codec="aac",
                    preset="medium",
                    threads=max((os.cpu_count() or 2) - 1, 1),
                    temp_audiofile=str(output_path.with_suffix(".temp-audio.m4a")),
                    remove_temp=True,
                    logger=None,
                )
        finally:
            for clip in reversed(clips_to_close):
                try:
                    clip.close()
                except Exception:
                    pass

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("Video rendering did not create a valid MP4 file.")
        return output_path

    def _prepare_background(self, clip: VideoFileClip, duration: float):
        fitted = self._fit_to_vertical(clip)
        fitted_duration = float(fitted.duration or 0)
        if fitted_duration <= 0:
            raise RuntimeError("Background video has an invalid duration.")

        if fitted_duration < duration:
            loops_needed = max(math.ceil(duration / fitted_duration), 1)
            fitted = fitted.fx(vfx.loop, n=loops_needed)

        return fitted.subclip(0, duration)

    def _fit_to_vertical(self, clip: VideoFileClip):
        target_ratio = self.WIDTH / self.HEIGHT
        source_ratio = clip.w / clip.h

        if source_ratio > target_ratio:
            resized = clip.resize(height=self.HEIGHT)
            return resized.crop(x_center=resized.w / 2, y_center=self.HEIGHT / 2, width=self.WIDTH, height=self.HEIGHT)

        resized = clip.resize(width=self.WIDTH)
        return resized.crop(x_center=self.WIDTH / 2, y_center=resized.h / 2, width=self.WIDTH, height=self.HEIGHT)

    def _build_text_overlays(
        self,
        temp_dir: Path,
        cues: list[SubtitleCue],
        cta_text: str,
        duration: float,
    ) -> list[ImageClip]:
        overlays: list[ImageClip] = []

        for cue in cues:
            image_path = temp_dir / f"subtitle_{cue.index:03d}.png"
            self._render_text_image(
                text=cue.text,
                output_path=image_path,
                font_size=70,
                max_width=940,
                fill=(255, 255, 255, 255),
                stroke_fill=(0, 0, 0, 230),
                stroke_width=6,
            )
            overlays.append(
                ImageClip(str(image_path))
                .set_start(cue.start)
                .set_duration(max(cue.end - cue.start, 0.1))
                .set_position(("center", int(self.HEIGHT * 0.66)))
            )

        cta = cta_text.strip()
        if cta:
            image_path = temp_dir / "cta.png"
            self._render_text_image(
                text=cta,
                output_path=image_path,
                font_size=82,
                max_width=920,
                fill=(255, 255, 255, 255),
                stroke_fill=(113, 24, 33, 255),
                stroke_width=7,
                background=(220, 38, 38, 215),
                padding_x=40,
                padding_y=26,
                rounded_radius=28,
            )
            cta_duration = min(3.0, duration)
            overlays.append(
                ImageClip(str(image_path))
                .set_start(max(duration - cta_duration, 0))
                .set_duration(cta_duration)
                .set_position(("center", int(self.HEIGHT * 0.80)))
            )

        return overlays

    def _render_text_image(
        self,
        text: str,
        output_path: Path,
        font_size: int,
        max_width: int,
        fill: tuple[int, int, int, int],
        stroke_fill: tuple[int, int, int, int],
        stroke_width: int,
        background: tuple[int, int, int, int] | None = None,
        padding_x: int = 28,
        padding_y: int = 20,
        rounded_radius: int = 18,
    ) -> None:
        layout = self._measure_text(text, font_size, max_width, padding_x, stroke_width)
        font, lines, bboxes, text_width, text_height, line_spacing = layout

        image_width = min(max_width, text_width + padding_x * 2)
        image_height = text_height + padding_y * 2
        image = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        if background:
            draw.rounded_rectangle(
                [(0, 0), (image_width - 1, image_height - 1)],
                radius=rounded_radius,
                fill=background,
            )

        y = padding_y
        for line, bbox in zip(lines, bboxes):
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            x = (image_width - line_width) / 2 - bbox[0]
            draw.text(
                (x, y - bbox[1]),
                line,
                font=font,
                fill=fill,
                stroke_width=stroke_width,
                stroke_fill=stroke_fill,
            )
            y += line_height + line_spacing

        image.save(output_path)

    def _measure_text(
        self,
        text: str,
        font_size: int,
        max_width: int,
        padding_x: int,
        stroke_width: int,
    ):
        current_size = font_size
        while current_size >= 34:
            font = self._load_font(current_size)
            measuring_image = Image.new("RGBA", (max_width, 1200), (0, 0, 0, 0))
            draw = ImageDraw.Draw(measuring_image)
            lines = self._wrap_text(draw, text, font, max_width - (padding_x * 2))
            line_spacing = int(current_size * 0.26)
            bboxes = [draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width) for line in lines]
            text_width = max((bbox[2] - bbox[0] for bbox in bboxes), default=1)
            text_height = sum((bbox[3] - bbox[1] for bbox in bboxes)) + line_spacing * max(len(lines) - 1, 0)

            if text_width + padding_x * 2 <= max_width:
                return font, lines, bboxes, text_width, text_height, line_spacing

            current_size -= 4

        return font, lines, bboxes, text_width, text_height, line_spacing

    def _wrap_text(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        words = text.split()
        if not words:
            return [""]

        lines: list[str] = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current = candidate
            else:
                lines.extend(self._split_oversized_word(draw, current, font, max_width))
                current = word
        lines.extend(self._split_oversized_word(draw, current, font, max_width))
        return lines

    def _split_oversized_word(
        self,
        draw: ImageDraw.ImageDraw,
        word: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> list[str]:
        bbox = draw.textbbox((0, 0), word, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return [word]

        chunks: list[str] = []
        current = ""
        for char in word:
            candidate = f"{current}{char}"
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if current and bbox[2] - bbox[0] > max_width:
                chunks.append(current)
                current = char
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks

    def _load_font(self, font_size: int) -> ImageFont.FreeTypeFont:
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]

        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, font_size)
            except OSError:
                continue

        return ImageFont.load_default()

    def _validate_inputs(self, background_video_path: Path, voice_audio_path: Path) -> None:
        if not background_video_path.is_file():
            raise RuntimeError(f"Background video file was not found: {background_video_path}")
        if not voice_audio_path.is_file():
            raise RuntimeError(f"Voice audio file was not found: {voice_audio_path}")
        if not shutil.which("ffmpeg"):
            raise RuntimeError("FFmpeg was not found in PATH. Install FFmpeg before rendering video.")
