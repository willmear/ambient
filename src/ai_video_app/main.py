from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_video_app.config import load_settings
from ai_video_app.models import FinalVideoRequest, GenerationRun, ImageGenerationRequest, VideoGenerationRequest
from ai_video_app.services.final_video_service import FinalVideoService
from ai_video_app.services.google_image_service import GoogleImageService
from ai_video_app.services.veo_service import VeoService


COSY_AMBIENT_IMAGE_PROMPT = (
    "A cosy ambient cabin interior at night, warm fireplace glow, soft rain on the window, "
    "candles on a wooden table, gentle shadows, cinematic composition, ultra-detailed, "
    "peaceful, relaxing atmosphere, no people, no text, no logos."
)


def main() -> None:
    """Run full Google image, Veo short video, and final looped video pipeline."""
    try:
        settings = load_settings()
        image_service = GoogleImageService(settings)
        veo_service = VeoService(settings)
        final_video_service = FinalVideoService(settings)
        run_id = uuid4()
        generation_run = GenerationRun(
            run_id=run_id,
            image_path=settings.image_output_dir / f"{run_id}.png",
            short_video_path=settings.video_output_dir / f"{run_id}.mp4",
            final_video_path=settings.final_output_dir / f"{run_id}.mp4",
        )

        image_request = ImageGenerationRequest(
            run_id=generation_run.run_id,
            prompt=COSY_AMBIENT_IMAGE_PROMPT,
            aspect_ratio=settings.default_aspect_ratio,
            output_path=generation_run.image_path,
        )
        generated_image = image_service.generate_image(image_request)

        video_request = VideoGenerationRequest(
            run_id=generation_run.run_id,
            prompt=COSY_AMBIENT_IMAGE_PROMPT,
            start_frame_path=generated_image.local_path,
            end_frame_path=generated_image.local_path,
            duration_seconds=settings.default_video_duration_seconds,
            aspect_ratio=settings.default_aspect_ratio,
            output_path=generation_run.short_video_path,
        )
        veo_video = veo_service.generate_video_from_frames(video_request)

        final_video_request = FinalVideoRequest(
            run_id=generation_run.run_id,
            input_video_path=veo_video.local_path,
            background_audio_path=settings.background_audio_path,
            duration_seconds=settings.final_video_duration_seconds,
            width=settings.final_video_width,
            height=settings.final_video_height,
            fps=settings.final_video_fps,
        )
        final_video = final_video_service.create_looped_final_video(final_video_request)

        print(f"run_id: {generation_run.run_id}")
        print(f"image path: {generated_image.local_path}")
        print(f"short video path: {veo_video.local_path}")
        print(f"final video path: {final_video.local_path}")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
