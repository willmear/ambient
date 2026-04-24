from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ImageGenerationRequest:
    prompt: str
    aspect_ratio: str
    output_name: str | None = None


@dataclass
class GeneratedImage:
    provider: str
    local_path: Path
    metadata: dict[str, Any]


@dataclass
class VideoGenerationRequest:
    prompt: str
    start_frame_path: Path
    end_frame_path: Path
    duration_seconds: int
    aspect_ratio: str
    output_name: str | None = None


@dataclass
class GeneratedVideo:
    provider: str
    local_path: Path
    remote_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
