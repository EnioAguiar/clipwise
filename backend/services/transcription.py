"""
Transcription service using OpenAI Whisper.

Provides word-level timestamps, segment structure, and JSON output saved to
/tmp/clipwise/<video_id>/ for integration with the ClipWise pipeline.
"""

import os
import json
import torch
import whisper

VIDEO_DIR = "/tmp/clipwise"


def transcribe_file(
    video_path: str,
    model_size: str = "base",
    language: str = None,
) -> dict:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"File not found: {video_path}")

    # Load Whisper model (auto-detects GPU/CPU)
    model = whisper.load_model(model_size)
    
    # Log device info
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute = "float16" if device == "cuda" else "float32"
    print(f"[WHISPER] Using device: {device}, compute: {compute}, model: {model_size}")

    # Transcribe with word timestamps
    result = model.transcribe(
        video_path,
        language=language,
        word_timestamps=True,
        verbose=False,
    )

    # Extract segment and word data
    segments_data = []
    words_data = []

    for seg in result.get("segments", []):
        segments_data.append({
            "id": seg.get("id"),
            "start": round(seg.get("start", 0), 3),
            "end": round(seg.get("end", 0), 3),
            "text": seg.get("text", "").strip(),
        })

        # Extract word-level timestamps
        seg_words = seg.get("words", [])
        if seg_words:
            for word in seg_words:
                words_data.append({
                    "word": word.get("word", "").strip(),
                    "start": round(word.get("start", 0), 3),
                    "end": round(word.get("end", 0), 3),
                    "confidence": round(word.get("probability", 0), 3),
                })

    # Build transcript text
    transcript = " ".join(s["text"] for s in segments_data)

    # Get duration from last segment
    duration = 0.0
    if segments_data:
        duration = segments_data[-1]["end"]

    # Detect language
    detected_lang = result.get("language", language or "en")

    output = {
        "transcript": transcript,
        "segments": segments_data,
        "words": words_data,
        "duration": round(duration, 3),
        "language": detected_lang,
    }

    # Save to /tmp/clipwise/<video_id>/transcript.json
    _save_transcript(video_path, output)

    return output


def _save_transcript(video_path: str, data: dict) -> None:
    """Save transcript JSON to the video's directory."""
    video_dir = os.path.dirname(video_path)
    video_id = os.path.basename(video_dir)

    os.makedirs(video_dir, exist_ok=True)

    transcript_path = os.path.join(video_dir, "transcript.json")
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)