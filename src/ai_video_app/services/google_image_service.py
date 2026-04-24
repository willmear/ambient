from __future__ import annotations

from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from PIL.Image import Image as PILImage

from ai_video_app.config import AppConfig
from ai_video_app.models import GeneratedImage, ImageGenerationRequest


class GoogleImageService:
    """Generate still images with Google's image generation models."""

    SUPPORTED_ASPECT_RATIOS = {"1:1", "16:9", "9:16", "3:4", "4:3"}

    def __init__(self, config: AppConfig) -> None:
        """Store app settings for image generation requests."""
        self._config = config

    def generate_image(self, request: ImageGenerationRequest) -> GeneratedImage:
        """Generate one image from prompt and save it locally."""
        self._validate_api_key()
        self._validate_request(request)

        client = genai.Client(api_key=self._config.google_api_key)
        output_path = self._build_output_path(request)

        try:
            response = client.models.generate_content(
                model=self._config.google_image_model,
                contents=[request.prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=request.aspect_ratio),
                ),
            )
            image = self._extract_generated_image(response)
            self._save_image(image, output_path)

            return GeneratedImage(
                run_id=request.run_id,
                provider="google-image",
                local_path=output_path,
                metadata={
                    "model": self._config.google_image_model,
                    "aspect_ratio": request.aspect_ratio,
                },
            )
        except ValueError:
            raise
        except OSError as exc:
            raise OSError(f"Failed to write generated image to {output_path}: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(self._format_provider_error(exc)) from exc
        finally:
            client.close()

    def _validate_api_key(self) -> None:
        """Fail fast when GOOGLE_API_KEY missing."""
        if not self._config.google_api_key:
            raise ValueError("Missing GOOGLE_API_KEY. Set it in .env before generating images.")

    def _validate_request(self, request: ImageGenerationRequest) -> None:
        """Reject unsupported request values before calling provider."""
        if not request.prompt.strip():
            raise ValueError("Image prompt must not be empty.")
        if len(request.prompt.strip()) < 3:
            raise ValueError("Image prompt is too short.")
        if request.aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            supported = ", ".join(sorted(self.SUPPORTED_ASPECT_RATIOS))
            raise ValueError(
                f"Unsupported image aspect_ratio={request.aspect_ratio!r}. Supported values: {supported}."
            )

    def _extract_generated_image(self, response: Any) -> PILImage:
        """Return first generated image from SDK response."""
        for part in getattr(response, "parts", []) or []:
            if getattr(part, "inline_data", None) is not None:
                return part.as_image()

        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                if getattr(part, "inline_data", None) is not None:
                    return part.as_image()

        raise RuntimeError("Google image generation completed but returned no image data.")

    def _save_image(self, image: PILImage, output_path: Path) -> None:
        """Persist generated image to disk."""
        try:
            image.save(output_path)
        except OSError:
            raise

    def _format_provider_error(self, exc: Exception) -> str:
        """Convert provider exceptions into short actionable messages."""
        message = str(exc)

        if "RESOURCE_EXHAUSTED" in message or "429" in message:
            return (
                "Google image generation quota exceeded for current API key or plan. "
                "Check Gemini API billing/quota, wait for retry window, or use different key/model."
            )

        return f"Google image generation failed: {message}"

    def _build_output_path(self, request: ImageGenerationRequest) -> Path:
        """Create safe output file path for generated image."""
        output_path = request.output_path or (self._config.image_output_dir / f"{request.run_id}.png")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            output_path = output_path.with_suffix(".png")

        return output_path
