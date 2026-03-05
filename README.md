# 🎬 YouTube Shorts Automation

A fully automated, end-to-end YouTube Shorts creation and upload system that
runs 24/7 via **GitHub Actions** — no server required, **100% free**.

🌐 **Live site:** [https://shahamar-official.github.io/yt-automation.github.io/](https://shahamar-official.github.io/yt-automation.github.io/)

---

## What it Does

Every 6 hours the pipeline:

1. 🔍 **Finds trending topics** from Google Trends and Reddit
2. ✍️ **Writes a professional script** using smart templates (no paid API)
3. 🎙️ **Converts the script to speech** using gTTS (Google Text-to-Speech — free)
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

Sign up at [pexels.com/api](https://www.pexels.com/api/) (free tier).

### 4. Add Secrets to GitHub

In your forked repository go to **Settings → Secrets and variables → Actions**
and add the following secrets:

| Secret name              | Value                                          |
|--------------------------|------------------------------------------------|
| `YOUTUBE_CLIENT_SECRET`  | Full JSON string of the OAuth2 client secret   |
| `YOUTUBE_TOKEN`          | JSON string with `access_token`, `refresh_token`|
| `PEXELS_API_KEY`         | Your Pexels API key                            |

### 5. Enable GitHub Actions

Go to the **Actions** tab in your repository and click **"I understand my
workflows, go ahead and enable them"** if prompted.

The workflow will run automatically every 6 hours, or you can trigger it
manually via **Actions → YouTube Shorts Automation → Run workflow**.

### 6. Enable GitHub Pages

Go to **Settings → Pages** and set the source to **GitHub Actions**.
The landing page will be published automatically on each push to `main`.

---

## How it Works — Step by Step

| Step | Module | Description |
|------|--------|-------------|
| 1 | `src/trending.py` | Fetches daily trending searches from Google Trends (US) and top posts from Reddit r/popular. Scores topics by cross-source appearance. |
| 2 | `src/scriptwriter.py` | Picks a curated script template and fills it with the trending topic. Returns title, narration, scene descriptions, tags, and YouTube description. |
| 3 | `src/tts.py` | Converts the narration to an MP3 file using gTTS (Google Text-to-Speech) and measures audio duration. |
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
| `TTS_LANG` | `"en"` | gTTS language code (e.g. `"en"`, `"es"`, `"fr"`) |
| `TTS_SLOW` | `False` | Slow speaking speed (`True` / `False`) |
| `YOUTUBE_CATEGORY_ID` | `"22"` | YouTube category (22 = People & Blogs) |
| `PRIVACY_STATUS` | `"public"` | Upload privacy (`public`, `unlisted`, `private`) |
| `MAX_VIDEOS_PER_RUN` | `1` | Videos per pipeline run |

---

## Cost Per Video

| Service | Usage | Cost |
|---------|-------|------|
| Script generation | Template engine | **$0.00** |
| Text-to-Speech | gTTS (Google TTS) | **$0.00** |
| Stock footage | Pexels API (free tier) | **$0.00** |
| CI / CD | GitHub Actions (~10 min/run) | **$0.00** |
| **Total** | | **$0.00** |

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
