"""Central configuration for the YouTube Shorts Automation pipeline."""

import os

# API Keys (loaded from GitHub Secrets / environment variables)
YOUTUBE_CLIENT_SECRET_JSON: str | None = os.getenv("YOUTUBE_CLIENT_SECRET")  # JSON string of OAuth2 client secret
YOUTUBE_TOKEN_JSON: str | None = os.getenv("YOUTUBE_TOKEN")  # JSON string of OAuth2 token
PEXELS_API_KEY: str | None = os.getenv("PEXELS_API_KEY")  # For stock footage

# Video settings
VIDEO_WIDTH: int = 1080
VIDEO_HEIGHT: int = 1920
VIDEO_FPS: int = 30
VIDEO_DURATION_TARGET: int = 45  # seconds target
FONT_SIZE: int = 60
FONT_COLOR: str = "white"
BG_MUSIC_VOLUME: float = 0.08

# TTS settings (gTTS — free Google Text-to-Speech)
TTS_LANG: str = "en"  # Language for gTTS
TTS_SLOW: bool = False  # Normal speaking speed

# Upload settings
YOUTUBE_CATEGORY_ID: str = "22"  # People & Blogs
PRIVACY_STATUS: str = "public"

# Scheduling
MAX_VIDEOS_PER_RUN: int = 1
