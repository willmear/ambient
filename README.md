# Ambient AI Video App

Generate cosy ambient videos with Google Gen AI and MoviePy for more money than it's worth.

## Full Pipeline

Current pipeline:

1. Generate cosy ambient image with Google image generation.
2. Use that image as start/end/reference frame for Veo.
3. Generate short AI video.
4. Use MoviePy to loop generated short video into 10-minute Full HD video.
5. Loop background audio from `assets/audio/Daytime Forrest Bonfire.mp3`.
6. Export final MP4 to `outputs/final/<uuid>.mp4`.

## Output Files

Each generation run uses one shared UUID.

Image, short video, and final video all share same UUID filename stem:

- `outputs/images/<uuid>.png`
- `outputs/videos/<uuid>.mp4`
- `outputs/final/<uuid>.mp4`

Each output type is stored in different folder.

## Requirements

- Python 3.11+ recommended
- local virtual environment
- `.env` file
- background audio file at `assets/audio/Daytime Forrest Bonfire.mp3`

Background audio file must exist before running app.

## Setup

Create virtual environment:

```bash
python3.11 -m venv venv
```

Activate virtual environment:

```bash
source venv/bin/activate
```

Install requirements:

```bash
pip install -r requirements.txt
```

Create local env file:

```bash
cp .env.example .env
```

Fill `.env` with real values for:

- `GOOGLE_API_KEY`
- `GOOGLE_IMAGE_MODEL`
- `GOOGLE_VEO_MODEL`

## Run

Run app:

```bash
python3 src/ai_video_app/main.py
```

App prints:

- `run_id`
- image path
- short video path
- final video path

## Git-Ignored Files

`.env` is required and is not committed.

Generated outputs are ignored by git:

- `outputs/`
- `temp/`
- `frames/`

Local virtual environments are ignored too:

- `venv/`
- `.venv/`

## Project Layout

```text
src/
  ai_video_app/
    config.py
    main.py
    models.py
    services/
      google_image_service.py
      veo_service.py
      final_video_service.py
```
