"""
tts.py — Text-to-speech generation using Google's free gTTS library.

Converts narration script text to an MP3 audio file and returns the file
path together with the audio duration in seconds.  Completely free — no
API keys required.
"""

import logging
import tempfile
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def _get_audio_duration(audio_path: Path) -> float:
    """Return the duration (in seconds) of an audio file.

    Tries ``mutagen`` first, then ``pydub`` as a fallback.
    Returns 0.0 if neither library is available.
    """
    # --- mutagen approach ---
    try:
        from mutagen.mp3 import MP3  # type: ignore[import]

        audio = MP3(str(audio_path))
        duration: float = audio.info.length
        logger.debug("Audio duration via mutagen: %.2f s", duration)
        return duration
    except Exception:  # noqa: BLE001
        pass

    # --- pydub approach ---
    try:
        from pydub import AudioSegment  # type: ignore[import]

        segment = AudioSegment.from_file(str(audio_path))
        duration = len(segment) / 1000.0
        logger.debug("Audio duration via pydub: %.2f s", duration)
        return duration
    except Exception:  # noqa: BLE001
        pass

    logger.warning("Could not determine audio duration; defaulting to 0.0 s")
    return 0.0


def generate_speech(script_text: str) -> tuple[Path, float]:
    """Generate TTS audio for *script_text* using Google's free gTTS.

    Args:
        script_text: The narration text to convert to speech.

    Returns:
        A tuple of ``(audio_path, duration_seconds)`` where *audio_path* is a
        :class:`pathlib.Path` pointing to the generated MP3 file.

    Raises:
        RuntimeError: If gTTS is not installed or the conversion fails.
    """
    try:
        from gtts import gTTS  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError("gTTS package is not installed — run: pip install gTTS") from exc

    # Write to a named temp file so it persists after the call
    tmp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    audio_path = Path(tmp_file.name)
    tmp_file.close()

    logger.info("Generating TTS for %d characters of script text…", len(script_text))
    try:
        tts = gTTS(
            text=script_text,
            lang=config.TTS_LANGUAGE,
            slow=False,
        )
        tts.save(str(audio_path))
    except Exception as exc:
        audio_path.unlink(missing_ok=True)
        raise RuntimeError(f"gTTS conversion failed: {exc}") from exc

    duration = _get_audio_duration(audio_path)
    logger.info("TTS audio saved to '%s' (%.2f s)", audio_path, duration)
    return audio_path, duration
