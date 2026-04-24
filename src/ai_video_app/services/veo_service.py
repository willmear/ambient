from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from ai_video_app.config import AppConfig
from ai_video_app.models import GeneratedVideo, VideoGenerationRequest


class VeoService:
    """Generate ambient videos from a local still image with Google Veo."""

    SUPPORTED_DURATIONS_SECONDS = {8}
    SUPPORTED_ASPECT_RATIOS = {"16:9", "9:16"}

    def __init__(self, config: AppConfig) -> None:
        """Store app settings for later video generation requests."""
        self._config = config

    def generate_video_from_frames(self, request: VideoGenerationRequest) -> GeneratedVideo:
        """Generate, poll, download, and save one Veo video from start/end frame paths."""
        self._validate_api_key()
        self._validate_request(request)

        output_path = self._build_output_path(request)
        client = genai.Client(api_key=self._config.google_api_key)

        try:
            source_image = types.Image.from_file(location=str(request.start_frame_path))
            last_frame_image = types.Image.from_file(location=str(request.end_frame_path))
            operation = client.models.generate_videos(
                model=self._config.google_veo_model,
                prompt=request.prompt,
                # Google Gen AI SDK supports image + last_frame for Veo interpolation.
                # If SDK/API falls back to single-image support in future, start_frame_path
                # remains primary image input and this code path is easy to simplify.
                image=source_image,
                config=types.GenerateVideosConfig(
                    number_of_videos=1,
                    duration_seconds=request.duration_seconds,
                    aspect_ratio=request.aspect_ratio,
                    generateAudio=False,
                    last_frame=last_frame_image,
                ),
            )
            operation = self._wait_for_completion(client, operation)
            generated_video = self._extract_generated_video(operation)
            file_resource = self._download_video_file(client, generated_video)
            file_resource.save(str(output_path))

            return GeneratedVideo(
                provider="veo",
                local_path=output_path,
                remote_url=getattr(file_resource, "uri", None),
                metadata={
                    "model": self._config.google_veo_model,
                    "start_frame_path": str(request.start_frame_path),
                    "end_frame_path": str(request.end_frame_path),
                    "duration_seconds": request.duration_seconds,
                    "aspect_ratio": request.aspect_ratio,
                    "generate_audio": False,
                    "operation_name": getattr(operation, "name", None),
                    "video_name": getattr(file_resource, "name", None),
                    "mime_type": getattr(file_resource, "mime_type", None),
                },
            )
        except TimeoutError:
            raise
        except (ValueError, FileNotFoundError):
            raise
        except Exception as exc:
            raise RuntimeError(f"Veo provider error: {exc}") from exc
        finally:
            client.close()

    def _validate_api_key(self) -> None:
        """Fail fast when GOOGLE_API_KEY missing."""
        if not self._config.google_api_key:
            raise ValueError("Missing GOOGLE_API_KEY. Set it in .env before using Veo.")

    def _validate_request(self, request: VideoGenerationRequest) -> None:
        """Reject unsupported request values before hitting provider."""
        if not request.prompt.strip():
            raise ValueError("Prompt must not be empty.")
        if not request.start_frame_path.exists():
            raise FileNotFoundError(f"Start frame does not exist: {request.start_frame_path}")
        if not request.start_frame_path.is_file():
            raise ValueError(f"Start frame path is not a file: {request.start_frame_path}")
        if not request.end_frame_path.exists():
            raise FileNotFoundError(f"End frame does not exist: {request.end_frame_path}")
        if not request.end_frame_path.is_file():
            raise ValueError(f"End frame path is not a file: {request.end_frame_path}")

        if request.duration_seconds not in self.SUPPORTED_DURATIONS_SECONDS:
            supported = ", ".join(str(value) for value in sorted(self.SUPPORTED_DURATIONS_SECONDS))
            raise ValueError(
                f"Unsupported Veo duration_seconds={request.duration_seconds}. "
                f"This app uses same image as first and last frame, and Veo interpolation supports: {supported}."
            )

        if request.aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            supported = ", ".join(sorted(self.SUPPORTED_ASPECT_RATIOS))
            raise ValueError(
                f"Unsupported Veo aspect_ratio={request.aspect_ratio!r}. Supported values: {supported}."
            )

    def _wait_for_completion(self, client: genai.Client, operation: Any) -> Any:
        """Poll Veo operation until done or timeout."""
        deadline = time.monotonic() + self._config.request_timeout

        while not getattr(operation, "done", False):
            if time.monotonic() >= deadline:
                name = getattr(operation, "name", "<unknown>")
                raise TimeoutError(
                    f"Timed out waiting for Veo operation {name} after {self._config.request_timeout} seconds."
                )

            time.sleep(self._config.poll_interval_seconds)
            operation = client.operations.get(operation)

        error = getattr(operation, "error", None)
        if error:
            message = getattr(error, "message", None) or str(error)
            raise RuntimeError(f"Veo generation failed: {message}")

        return operation

    def _extract_generated_video(self, operation: Any) -> Any:
        """Return generated video entry from finished operation."""
        response = getattr(operation, "response", None)
        videos = getattr(response, "generated_videos", None)

        if not videos:
            raise RuntimeError("Veo completed but returned no generated video.")

        generated_video = videos[0]
        video_file = getattr(generated_video, "video", None)
        if video_file is None:
            raise RuntimeError("Veo completed but response contained no downloadable video file.")

        return generated_video

    def _download_video_file(self, client: genai.Client, generated_video: Any) -> Any:
        """Download video bytes through official SDK."""
        video_file = generated_video.video
        client.files.download(file=video_file)

        if not hasattr(video_file, "save"):
            raise RuntimeError("Veo SDK did not return savable video content.")

        return video_file

    def _build_output_path(self, request: VideoGenerationRequest) -> Path:
        """Create safe output file path inside configured output directory."""
        self._config.video_output_dir.mkdir(parents=True, exist_ok=True)

        if request.output_name:
            filename = request.output_name
        else:
            prompt_slug = self._slugify(request.prompt)[:60] or "veo-video"
            timestamp = int(time.time())
            filename = f"{prompt_slug}-{timestamp}.mp4"

        if not filename.endswith(".mp4"):
            filename = f"{filename}.mp4"

        return self._config.video_output_dir / filename

    def _slugify(self, value: str) -> str:
        """Convert prompt into short filesystem-safe slug."""
        cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
        return cleaned.strip("-")
