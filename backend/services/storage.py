"""
Storage service for video/file management.

Handles saving uploaded files and YouTube downloads to /tmp/clipwise/
with unique IDs and metadata tracking.
"""

import os
import uuid
import subprocess
from typing import Optional
from fastapi import UploadFile

VIDEO_DIR = "/tmp/clipwise"

# In-memory metadata store: {file_id: {path, filename, duration}}
_video_metadata: dict = {}


def save_upload(file: UploadFile) -> dict:
    """
    Save an uploaded video file to /tmp/clipwise/<uuid>/original.<ext>.

    Returns {file_id, path, filename, duration}.
    """
    if not file.filename:
        raise ValueError("No filename provided")

    # Determine extension
    ext = os.path.splitext(file.filename)[1] or ".mp4"
    if not ext.startswith("."):
        ext = "." + ext

    # Generate unique ID and path
    file_id = str(uuid.uuid4())
    dest_dir = os.path.join(VIDEO_DIR, file_id)
    os.makedirs(dest_dir, exist_ok=True)

    dest_path = os.path.join(dest_dir, f"original{ext}")

    # Save file content
    content = file.file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    # Get duration using ffprobe
    duration = _get_duration(dest_path)

    metadata = {
        "file_id": file_id,
        "path": dest_path,
        "filename": file.filename,
        "duration": duration,
    }

    _video_metadata[file_id] = metadata
    return metadata


def save_youtube(url: str) -> dict:
    """
    Download YouTube video audio via yt-dlp and save to /tmp/clipwise/<uuid>/.

    Returns {file_id, path, filename, duration}.
    """
    file_id = str(uuid.uuid4())
    dest_dir = os.path.join(VIDEO_DIR, file_id)
    os.makedirs(dest_dir, exist_ok=True)

    output_template = os.path.join(dest_dir, "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "wav",
        "-o", output_template,
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr}")

    # Find the downloaded file
    downloaded_files = []
    for f in os.listdir(dest_dir):
        if os.path.isfile(os.path.join(dest_dir, f)):
            downloaded_files.append(f)

    if not downloaded_files:
        raise RuntimeError(f"No file downloaded for URL: {url}")

    # Use the first audio file found
    dest_path = os.path.join(dest_dir, downloaded_files[0])
    filename = downloaded_files[0]

    # Get duration
    duration = _get_duration(dest_path)

    metadata = {
        "file_id": file_id,
        "path": dest_path,
        "filename": filename,
        "duration": duration,
    }

    _video_metadata[file_id] = metadata
    return metadata


def get_video_info(file_id: str) -> Optional[dict]:
    """
    Retrieve metadata for a saved video by file_id.

    Returns metadata dict or None if not found.
    """
    return _video_metadata.get(file_id)


def _get_duration(file_path: str) -> float:
    """Get video/audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        file_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
    except Exception:
        pass
    return 0.0