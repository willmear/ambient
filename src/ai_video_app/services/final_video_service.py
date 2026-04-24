from __future__ import annotations

import math
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from moviepy import AudioFileClip, VideoFileClip, afx, concatenate_audioclips, concatenate_videoclips

from ai_video_app.config import AppConfig
from ai_video_app.models import FinalVideoRequest, FinalVideoResult


class FinalVideoService:
    """Create long-form final videos from short generated clips and background audio."""

    def __init__(self, config: AppConfig) -> None:
        """Store app settings for final video export."""
        self._config = config

    def create_looped_final_video(self, request: FinalVideoRequest) -> FinalVideoResult:
        """Loop video and audio to exact target duration, then export final MP4."""
        self._validate_request(request)
        output_path = self._build_output_path(request)

        with ExitStack() as stack:
            try:
                source_video = VideoFileClip(str(request.input_video_path))
                stack.callback(source_video.close)

                background_audio = AudioFileClip(str(request.background_audio_path))
                stack.callback(background_audio.close)
            except Exception as exc:
                raise RuntimeError(f"MoviePy failed to load media: {exc}") from exc

            if not source_video.duration or source_video.duration <= 0:
                raise RuntimeError("Input video has invalid duration.")
            if not background_audio.duration or background_audio.duration <= 0:
                raise RuntimeError("Background audio has invalid duration.")

            try:
                video_base = source_video.without_audio()
                stack.callback(video_base.close)
                looped_video = self._loop_video_clip(video_base, request.duration_seconds)
                stack.callback(looped_video.close)
                trimmed_video = looped_video.subclipped(0, request.duration_seconds)
                stack.callback(trimmed_video.close)
                sized_video = self._resize_and_crop_to_full_hd(trimmed_video, request.width, request.height)
                stack.callback(sized_video.close)
            except Exception as exc:
                raise RuntimeError(f"MoviePy failed to prepare video track: {exc}") from exc

            try:
                looped_audio = self._loop_audio_clip(background_audio, request.duration_seconds)
                stack.callback(looped_audio.close)
                trimmed_audio = looped_audio.subclipped(0, request.duration_seconds)
                stack.callback(trimmed_audio.close)
            except Exception as exc:
                raise RuntimeError(f"MoviePy failed to prepare audio track: {exc}") from exc

            try:
                final_clip = sized_video.with_audio(trimmed_audio).with_duration(request.duration_seconds)
                stack.callback(final_clip.close)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                final_clip.write_videofile(
                    str(output_path),
                    fps=request.fps,
                    codec="libx264",
                    audio_codec="aac",
                    temp_audiofile=str(output_path.with_suffix(".temp-audio.m4a")),
                    remove_temp=True,
                )
            except Exception as exc:
                raise RuntimeError(f"MoviePy failed to export final video: {exc}") from exc

        return FinalVideoResult(
            run_id=request.run_id,
            local_path=output_path,
            duration_seconds=request.duration_seconds,
            metadata={
                "width": request.width,
                "height": request.height,
                "fps": request.fps,
                "video_codec": "libx264",
                "audio_codec": "aac",
                "background_audio_path": str(request.background_audio_path),
                "input_video_path": str(request.input_video_path),
            },
        )

    def _validate_request(self, request: FinalVideoRequest) -> None:
        """Validate paths and export settings before loading media."""
        if not request.input_video_path.exists():
            raise FileNotFoundError(f"Input video does not exist: {request.input_video_path}")
        if not request.input_video_path.is_file():
            raise ValueError(f"Input video path is not a file: {request.input_video_path}")
        if not request.background_audio_path.exists():
            raise FileNotFoundError(f"Background audio does not exist: {request.background_audio_path}")
        if not request.background_audio_path.is_file():
            raise ValueError(f"Background audio path is not a file: {request.background_audio_path}")
        if request.duration_seconds <= 0:
            raise ValueError("Final video duration must be positive.")
        if request.width <= 0:
            raise ValueError("Final video width must be positive.")
        if request.height <= 0:
            raise ValueError("Final video height must be positive.")
        if request.fps <= 0:
            raise ValueError("Final video fps must be positive.")

    def _build_output_path(self, request: FinalVideoRequest) -> Path:
        """Build final output path from shared run UUID."""
        self._config.final_output_dir.mkdir(parents=True, exist_ok=True)
        return self._config.final_output_dir / f"{request.run_id}.mp4"

    def _loop_video_clip(self, clip: VideoFileClip, target_duration: int) -> Any:
        """Loop video clip to at least target duration using helper or concat fallback."""
        source_duration = getattr(clip, "duration", None)
        if not source_duration or source_duration <= 0:
            raise RuntimeError("Source video duration missing or zero.")

        loop_count = max(1, math.ceil(target_duration / source_duration))
        return concatenate_videoclips([clip] * loop_count, method="chain")

    def _loop_audio_clip(self, clip: AudioFileClip, target_duration: int) -> Any:
        """Loop audio clip to at least target duration using helper or concat fallback."""
        source_duration = getattr(clip, "duration", None)
        if not source_duration or source_duration <= 0:
            raise RuntimeError("Source audio duration missing or zero.")

        try:
            return clip.with_effects([afx.AudioLoop(duration=target_duration)])
        except Exception:
            pass

        loop_count = max(1, math.ceil(target_duration / source_duration))
        return concatenate_audioclips([clip] * loop_count)

    def _resize_and_crop_to_full_hd(self, clip: VideoFileClip, width: int, height: int) -> Any:
        """Resize to cover frame, then center-crop to exact output size."""
        scale = max(width / clip.w, height / clip.h)
        resized_clip = clip.resized(scale)

        x_center = resized_clip.w / 2
        y_center = resized_clip.h / 2

        return resized_clip.cropped(
            x_center=x_center,
            y_center=y_center,
            width=width,
            height=height,
        )
