# 🎬 YouTube Shorts Automation

A fully automated, end-to-end YouTube Shorts creation and upload system that
runs 24/7 via **GitHub Actions** — no server required, **100% free**.

> **$0.00 per video** — No paid APIs. Uses Google TTS, template-based scripts,
> free Pexels stock footage, and GitHub Actions.

---

## What it Does

Every 6 hours the pipeline:

1. 🔍 **Finds trending topics** from Google Trends and Reddit
2. ✍️ **Writes a professional script** using smart templates with hooks, narration, and CTAs
3. 🎙️ **Converts the script to speech** using Google TTS (gTTS — free)
4. 🎬 **Creates a vertical 1080 × 1920 video** with Pexels stock footage and animated captions
5. 🖼️ **Generates an eye-catching thumbnail** with Pillow
6. 🚀 **Uploads to YouTube** with optimised title, tags, description, and thumbnail

---

## Architecture

```
GitHub Actions (cron: every 6 h)
        │
        ▼
src/pipeline.py  ──────────────────────────────────────────────┐
        │                                                       │
        ├─► src/trending.py      (Google Trends + Reddit)      │
        │         │ trending topic                              │
        ├─► src/scriptwriter.py  (Template engine — free)      │
        │         │ title, script, scenes, tags, description    │
        ├─► src/tts.py           (gTTS — free)                 │
        │         │ audio MP3 + duration                        │
        ├─► src/video_creator.py (Pexels API + MoviePy)        │
        │         │ 1080×1920 MP4                               │
        ├─► src/thumbnail.py     (Pillow)                       │
        │         │ 1280×720 JPEG                               │
        └─► src/uploader.py      (YouTube Data API v3)          │
                  │ video ID + URL                              │
                  └───────────────────────────────────────────►─┘
```

---

## Setup

### 1. Fork this Repository

Click **Fork** at the top right of this page.

### 2. Set Up YouTube OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project and enable the **YouTube Data API v3**
3. Create **OAuth 2.0 Client ID** credentials (Desktop app)
4. Download the client secret JSON
5. Run the one-time OAuth flow locally to generate a token JSON:

```bash
pip install google-auth-oauthlib
python - <<'EOF'
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",
    scopes=["https://www.googleapis.com/auth/youtube.upload"]
)
creds = flow.run_local_server(port=0)
import json
print(json.dumps({
    "access_token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
}))
EOF
```

### 3. Get a Pexels API Key

Sign up at [pexels.com/api](https://www.pexels.com/api/) (free tier available).

### 4. Add Secrets to GitHub

In your forked repository go to **Settings → Secrets and variables → Actions**
and add the following secrets:

| Secret name              | Value                                          |
|--------------------------|------------------------------------------------|
| `YOUTUBE_CLIENT_SECRET`  | Full JSON string of the OAuth2 client secret   |
| `YOUTUBE_TOKEN`          | JSON string with `access_token`, `refresh_token`|
| `PEXELS_API_KEY`         | Your Pexels API key (free)                     |

> **Note:** No OpenAI API key is needed! Script generation and TTS are
> handled by free alternatives.

### 5. Enable GitHub Actions

Go to the **Actions** tab in your repository and click **"I understand my
workflows, go ahead and enable them"** if prompted.

The workflow will run automatically every 6 hours, or you can trigger it
manually via **Actions → YouTube Shorts Automation → Run workflow**.

---

## How it Works — Step by Step

| Step | Module | Description |
|------|--------|-------------|
| 1 | `src/trending.py` | Fetches daily trending searches from Google Trends (US) and top posts from Reddit r/popular. Scores topics by cross-source appearance. |
| 2 | `src/scriptwriter.py` | Generates engaging scripts using a template engine with hooks, body variations, CTAs, scene descriptions, tags, and descriptions. Fully deterministic — no API key needed. |
| 3 | `src/tts.py` | Converts the narration to an MP3 file using Google's free gTTS library and measures audio duration. |
| 4 | `src/video_creator.py` | Queries Pexels for portrait video clips per scene, assembles them with MoviePy, adds captions, overlays audio, and exports to MP4. |
| 5 | `src/thumbnail.py` | Creates a gradient 1280 × 720 JPEG thumbnail with the video title and a topic emoji using Pillow. |
| 6 | `src/uploader.py` | Uploads the video via the YouTube Data API v3 resumable upload endpoint, then attaches the thumbnail. |

---

## Customisation

Edit `config.py` to change:

| Setting | Default | Description |
|---------|---------|-------------|
| `VIDEO_FPS` | `30` | Output frame rate |
| `FONT_SIZE` | `60` | Caption font size (px) |
| `BG_MUSIC_VOLUME` | `0.08` | Background music volume (0.0 = off). Place an MP3 at the path set by `BG_MUSIC_PATH` to enable. |
| `BG_MUSIC_PATH` | `"assets/bg_music.mp3"` | Path to the background music MP3 file (relative to the repo root). |
| `TTS_LANGUAGE` | `"en"` | gTTS language code (`en`, `es`, `fr`, `de`, `hi`, etc.) |
| `YOUTUBE_CATEGORY_ID` | `"22"` | YouTube category (22 = People & Blogs) |
| `PRIVACY_STATUS` | `"public"` | Upload privacy (`public`, `unlisted`, `private`) |
| `MAX_VIDEOS_PER_RUN` | `1` | Videos per pipeline run |

---

## Cost Breakdown (per video)

| Service | Usage | Cost |
|---------|-------|------|
| Template engine | Script generation | **Free** |
| gTTS | Voice narration | **Free** |
| Pexels API | Stock footage | **Free** |
| Google Trends | Trending topics | **Free** |
| Reddit | Trending topics | **Free** |
| GitHub Actions | ~10 min / run | **Free** (2,000 min/month included) |
| **Total** | | **$0.00 / video** |

---

## Disclaimer

This tool is intended for educational and creative purposes. Ensure your use
of the YouTube API complies with [YouTube's Terms of Service](https://www.youtube.com/t/terms)
and the [YouTube API Services Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service).
You are solely responsible for the content uploaded by this automation.
Always review the content before publishing publicly if possible.

---

## License

This project is licensed under the **MIT License**.
See [LICENSE](LICENSE) for details.
