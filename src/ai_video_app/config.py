from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    output_dir: Path
    image_output_dir: Path
    video_output_dir: Path
    final_output_dir: Path
    audio_dir: Path
    default_aspect_ratio: str
    default_video_duration_seconds: int
    final_video_duration_seconds: int
    final_video_width: int
    final_video_height: int
    final_video_fps: int
    background_audio_filename: str
    google_api_key: str
    google_image_model: str
    google_veo_model: str
    request_timeout: int
    poll_interval_seconds: int

    def validate_required_api_keys(self) -> None:
        if not self.google_api_key:
            raise ValueError("Missing required environment variable: GOOGLE_API_KEY")

    def validate_video_settings(self) -> None:
        if self.final_video_duration_seconds <= 0:
            raise ValueError("FINAL_VIDEO_DURATION_SECONDS must be positive.")
        if self.final_video_width <= 0:
            raise ValueError("FINAL_VIDEO_WIDTH must be positive.")
        if self.final_video_height <= 0:
            raise ValueError("FINAL_VIDEO_HEIGHT must be positive.")

    @property
    def background_audio_path(self) -> Path:
        return self.audio_dir / self.background_audio_filename


AppConfig = Settings


def _get_path(value: str, default: str) -> Path:
    return Path(value or default).expanduser().resolve()


def load_settings() -> Settings:
    output_dir = _get_path(os.getenv("OUTPUT_DIR", ""), "outputs")
    image_output_dir = _get_path(os.getenv("IMAGE_OUTPUT_DIR", ""), str(output_dir / "images"))
    video_output_dir = _get_path(os.getenv("VIDEO_OUTPUT_DIR", ""), str(output_dir / "videos"))
    final_output_dir = _get_path(os.getenv("FINAL_OUTPUT_DIR", ""), str(output_dir / "final"))
    audio_dir = _get_path(os.getenv("AUDIO_DIR", ""), "assets/audio")

    output_dir.mkdir(parents=True, exist_ok=True)
    image_output_dir.mkdir(parents=True, exist_ok=True)
    video_output_dir.mkdir(parents=True, exist_ok=True)
    final_output_dir.mkdir(parents=True, exist_ok=True)

    settings = Settings(
        output_dir=output_dir,
        image_output_dir=image_output_dir,
        video_output_dir=video_output_dir,
        final_output_dir=final_output_dir,
        audio_dir=audio_dir,
        default_aspect_ratio=os.getenv("DEFAULT_ASPECT_RATIO", "16:9").strip() or "16:9",
        default_video_duration_seconds=int(os.getenv("DEFAULT_VIDEO_DURATION_SECONDS", "8")),
        final_video_duration_seconds=int(os.getenv("FINAL_VIDEO_DURATION_SECONDS", "600")),
        final_video_width=int(os.getenv("FINAL_VIDEO_WIDTH", "1920")),
        final_video_height=int(os.getenv("FINAL_VIDEO_HEIGHT", "1080")),
        final_video_fps=int(os.getenv("FINAL_VIDEO_FPS", "30")),
        background_audio_filename=os.getenv("BACKGROUND_AUDIO_FILENAME", "Daytime Forrest Bonfire.mp3").strip()
        or "Daytime Forrest Bonfire.mp3",
        google_api_key=os.getenv("GOOGLE_API_KEY", "").strip(),
        google_image_model=os.getenv("GOOGLE_IMAGE_MODEL", "").strip() or "gemini-3.1-flash-image-preview",
        google_veo_model=os.getenv("GOOGLE_VEO_MODEL", "veo-3.1-generate-preview").strip() or "veo-3.1-generate-preview",
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "300")),
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "10")),
    )

    settings.validate_required_api_keys()
    settings.validate_video_settings()
    return settings


def load_config() -> Settings:
    return load_settings()
