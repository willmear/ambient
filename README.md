# Ambient AI Video App

Internal personal app for generating cosy ambient visuals with Google APIs.

## Pipeline

Current app uses Google-only flow:

- generate cosy ambient still image with Google image generation
- save generated image locally
- reuse same image as both start and end frame/reference for Google Veo video generation
- save generated video locally

Kling is no longer used.

MoviePy looping and editing will be added later.

## Requirements

- Python 3.11+
- local virtual environment
- `.env` file with Google API settings

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
PYTHONPATH=src python -m ai_video_app.main
```

App will:

- load settings
- generate cosy ambient still image
- save image under `outputs/images/`
- reuse same image as both start and end frame for Veo
- save video under `outputs/videos/`
- print saved image path and video path

## Git-Ignored Local Files

These are ignored by git:

- `.env`
- `venv/`
- `.venv/`
- `outputs/`
- `temp/`
- `frames/`

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
```
