# AI Affiliate Video Builder

Python desktop MVP for generating one short vertical affiliate video from product information, a background video, Vietnamese voice-over, subtitles, and a final CTA.

## Features

- PySide6 desktop UI
- OpenAI script generation when `OPENAI_API_KEY` is available
- Local mock Vietnamese script generation when `OPENAI_API_KEY` is missing
- Vietnamese voice-over with `edge-tts`
- Estimated SRT subtitle generation from the script and MP3 duration
- 1080x1920 MP4 rendering with MoviePy and FFmpeg
- SQLite project history in the OS app data folder, with optional `AIVB_DB_PATH` override

## Setup

Requires Python 3.11+.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install FFmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg
```

On Windows, install FFmpeg from https://ffmpeg.org/download.html and make sure `ffmpeg` is available in `PATH`.

## OpenAI Configuration

The app reads the API key from `OPENAI_API_KEY`. Do not hardcode keys in the project.

```bash
export OPENAI_API_KEY="your_api_key_here"
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

Optional model override:

```bash
export OPENAI_MODEL="gpt-4o-mini"
```

If `OPENAI_API_KEY` is not set, the app still runs and uses a mock Vietnamese affiliate script generator.

## Run

```bash
source .venv/bin/activate
python main.py
```

In the app:

1. Enter product name, benefits, target audience, style, and CTA.
2. Select a background video file.
3. Select an output folder.
4. Click **Generate Video**.

Each render creates a timestamped folder containing:

- `voiceover.mp3`
- `subtitles.srt`
- `affiliate_video.mp4`

## Notes

- This MVP renders one video at a time.
- Text-to-video generation, ComfyUI, and batch rendering are intentionally not included yet.
- Background clips are resized and center-cropped to vertical 9:16.
- Voice generation uses the Vietnamese `vi-VN-HoaiMyNeural` voice by default.
- `edge-tts` uses Microsoft's online TTS service, so voice generation requires network access.
- Project history is saved in the OS app data folder. Set `AIVB_DB_PATH` if you want to store the SQLite file somewhere else.
