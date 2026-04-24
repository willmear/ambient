from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID


@dataclass
class GenerationRun:
    run_id: UUID
    image_path: Path
    short_video_path: Path
    final_video_path: Path


@dataclass
class ImageGenerationRequest:
    run_id: UUID
    prompt: str
    aspect_ratio: str
    output_path: Path | None = None


@dataclass
class GeneratedImage:
    run_id: UUID
    provider: str
    local_path: Path
    metadata: dict[str, Any]


@dataclass
class VideoGenerationRequest:
    run_id: UUID
    prompt: str
    start_frame_path: Path
    end_frame_path: Path
    duration_seconds: int
    aspect_ratio: str
    output_path: Path | None = None


@dataclass
class GeneratedVideo:
    run_id: UUID
    provider: str
    local_path: Path
    remote_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FinalVideoRequest:
    run_id: UUID
    input_video_path: Path
    background_audio_path: Path
    duration_seconds: int = 600
    width: int = 1920
    height: int = 1080
    fps: int = 30


@dataclass
class FinalVideoResult:
    run_id: UUID
    local_path: Path
    duration_seconds: int
    metadata: dict[str, Any] = field(default_factory=dict)
