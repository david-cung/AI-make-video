# AI Affiliate Video Builder

Python desktop MVP for generating one short vertical affiliate video from product information, a background video, Vietnamese voice-over, subtitles, and a final CTA.

## Features

- PySide6 desktop UI
- OpenAI script generation when `OPENAI_API_KEY` is available
- Local mock Vietnamese script generation when `OPENAI_API_KEY` is missing
- Five selectable affiliate video templates
- Vietnamese voice-over with `edge-tts`
- Estimated SRT subtitle generation from the script and MP3 duration
- 1080x1920 MP4 rendering with MoviePy and FFmpeg
- SQLite project history in the OS app data folder, with optional `AIVB_DB_PATH` override

## Setup

Requires Python 3.11+ and FFmpeg.

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

Windows PowerShell:

```powershell
$env:OPENAI_MODEL="gpt-4o-mini"
```

If `OPENAI_API_KEY` is not set, the app still runs and uses a mock Vietnamese affiliate script generator.

## Run

```bash
source .venv/bin/activate
python main.py
```

In the app:

1. Enter product name, benefits, and target audience.
2. Choose a **Video Template** and video style.
3. Enter CTA text.
4. Select a background video file.
5. Select an output folder.
6. Click **Generate Video**.

## Video Templates

Choose a template from the **Video Template** dropdown before generating. The selected template changes the script prompt, the mock fallback script, the script preview, and `metadata.json`.

- **Problem Solution**: Best for products that solve a clear everyday pain point. Structure: hook, problem, solution, benefit, CTA.
- **Top 3 Benefits**: Best when a product has several easy-to-scan selling points. Structure: "3 reasons why...", benefit 1, benefit 2, benefit 3, CTA.
- **Before After**: Best for showing a simple contrast between an old frustrating workflow and a smoother experience. Structure: hook, before, after, CTA.
- **Honest Review**: Best for creator-style affiliate videos that need to feel balanced and trustworthy. Structure: “I tried this...”, what it is, what I liked, what could be better, who it is for, CTA.
- **TikTok Hook Test**: Best for more aggressive short-form openings. The generator tests 3 hook ideas internally, picks the strongest one, then writes the final short script using that hook.

Each render creates a timestamped folder containing:

- `script.txt`
- `voice.mp3`
- `subtitles.srt`
- `output.mp4`
- `metadata.json`

Folder format:

```text
YYYYMMDD_HHMMSS_product_slug
```

`metadata.json` includes the selected template, template structure, product inputs, generated script, output video path, and created timestamp.

## Logs and History

- Project history is saved in the OS app data folder.
- Technical errors are logged to `logs/app.log` inside the same app data folder.
- Set `AIVB_DB_PATH` to choose a custom SQLite history file.
- Set `AIVB_LOG_PATH` to choose a custom log file.

## Notes

- This MVP renders one video at a time.
- Text-to-video generation, ComfyUI, and batch rendering are intentionally not included yet.
- Background clips are resized and center-cropped to vertical 9:16.
- Voice generation uses the Vietnamese `vi-VN-HoaiMyNeural` voice by default.
- `edge-tts` uses Microsoft's online TTS service, so voice generation requires network access.

## Troubleshooting

- `ModuleNotFoundError: PySide6`: activate the venv and run `pip install -r requirements.txt`.
- `FFmpeg was not found in PATH`: install FFmpeg and restart the terminal so `ffmpeg -version` works.
- Voice generation fails: check internet access; `edge-tts` needs access to Microsoft's online TTS service.
- OpenAI script generation fails: verify `OPENAI_API_KEY`, or unset it to use the mock script generator.
- Output folder error: choose a folder you can write to, such as Desktop, Documents, or a dedicated exports folder.
- The UI opens but rendering is slow: use a short background clip for testing; final export is 1080x1920 and can take time.
