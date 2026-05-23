"""
Transcription service using Faster Whisper.

Provides word-level timestamps, segment structure, and JSON output saved to
/tmp/clipwise/<video_id>/ for integration with the ClipWise pipeline.
"""

import os
import json
from typing import Optional
from faster_whisper import WhisperModel


VIDEO_DIR = "/tmp/clipwise"


def transcribe_file(
    video_path: str,
    model_size: str = "base",
    language: Optional[str] = None,
) -> dict:
    """
    Transcribe a video/audio file with word-level timestamps.

    Args:
        video_path: Path to video/audio file
        model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
        language: Optional language code (auto-detect if None)

    Returns:
        {
            "transcript": str,
            "segments": [{id, start, end, text}, ...],
            "words": [{word, start, end, confidence}, ...],
            "duration": float,
            "language": str,
        }
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"File not found: {video_path}")

    # Load Faster Whisper model (CPU only to avoid CUDA library issues)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    # Transcribe with word timestamps
    segments, info = model.transcribe(
        video_path,
        language=language,
        word_timestamps=True,
        vad_filter=True,  # Voice activity detection for cleaner segments
    )

    # Extract segment and word data
    segments_data = []
    words_data = []

    for seg in segments:
        segments_data.append({
            "id": seg.id,
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
        })

        # Extract word-level timestamps
        if seg.words:
            for word in seg.words:
                words_data.append({
                    "word": word.word.strip(),
                    "start": round(word.start, 3),
                    "end": round(word.end, 3),
                    "confidence": round(word.probability, 3),
                })

    # Build transcript text
    transcript = " ".join(s["text"] for s in segments_data)

    # Get duration from last segment or info
    duration = 0.0
    if info.duration:
        duration = info.duration
    elif segments_data:
        duration = segments_data[-1]["end"]

    # Detect language
    detected_lang = info.language if info.language else (language or "en")

    result = {
        "transcript": transcript,
        "segments": segments_data,
        "words": words_data,
        "duration": round(duration, 3),
        "language": detected_lang,
    }

    # Save to /tmp/clipwise/<video_id>/transcript.json
    _save_transcript(video_path, result)

    return result


def _save_transcript(video_path: str, data: dict) -> None:
    """Save transcript JSON to the video's directory."""
    # Extract video_id from path like /tmp/clipwise/<video_id>/original.mp4
    video_dir = os.path.dirname(video_path)
    video_id = os.path.basename(video_dir)

    # Create directory if needed
    os.makedirs(video_dir, exist_ok=True)

    # Save transcript.json
    transcript_path = os.path.join(video_dir, "transcript.json")
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)