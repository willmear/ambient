from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_video_app.config import load_settings
from ai_video_app.models import ImageGenerationRequest, VideoGenerationRequest
from ai_video_app.services.google_image_service import GoogleImageService
from ai_video_app.services.veo_service import VeoService


COSY_AMBIENT_IMAGE_PROMPT = (
    "A cosy ambient cabin interior at night, warm fireplace glow, soft rain on the window, "
    "candles on a wooden table, gentle shadows, cinematic composition, ultra-detailed, "
    "peaceful, relaxing atmosphere, no people, no text, no logos."
)


def main() -> None:
    """Run simple Google-only still-image-to-video generation flow."""
    try:
        settings = load_settings()
        image_service = GoogleImageService(settings)
        veo_service = VeoService(settings)

        image_request = ImageGenerationRequest(
            prompt=COSY_AMBIENT_IMAGE_PROMPT,
            aspect_ratio=settings.default_aspect_ratio,
            output_name="cosy_ambient_still.png",
        )
        generated_image = image_service.generate_image(image_request)
        print(f"Saved image to: {generated_image.local_path}")

        video_request = VideoGenerationRequest(
            prompt=COSY_AMBIENT_IMAGE_PROMPT,
            start_frame_path=generated_image.local_path,
            end_frame_path=generated_image.local_path,
            duration_seconds=settings.default_video_duration_seconds,
            aspect_ratio=settings.default_aspect_ratio,
            output_name="cosy_ambient_video.mp4",
        )
        veo_video = veo_service.generate_video_from_frames(video_request)
        print(f"Saved video to: {veo_video.local_path}")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
