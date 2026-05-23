---
phase: 01-upload-transcription-energy
plan: 01
subsystem: backend
tags: [upload, youtube, storage, video]
dependency_graph:
  requires: []
  provides: [UPLD-01, UPLD-02, UPLD-03, UPLD-04]
  affects: [backend/main.py, backend/services/storage.py]
tech_stack:
  added: [yt-dlp>=2024.0.0]
  patterns: [FastAPI UploadFile, subprocess yt-dlp, in-memory metadata store]
key_files:
  created:
    - backend/services/__init__.py
    - backend/services/storage.py
  modified:
    - backend/main.py
    - backend/requirements.txt
decisions:
  - Used UUID-based file_id generation for unique identification
  - yt-dlp downloads audio as WAV format for maximum compatibility
  - In-memory metadata dict for session-based tracking
metrics:
  duration_minutes: ~2
  completed_date: "2026-05-23T17:13:44Z"
  tasks_completed: 3
---

# Phase 01 Plan 01: Upload + Transcription Energy - Summary

## One-liner

Video upload backend accepting file and YouTube URL input with storage to `/tmp/clipwise/` and metadata return.

## Completed Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Create backend services directory structure | `cd2407bc` | `backend/services/__init__.py`, `backend/services/storage.py` |
| 2 | Add /upload and /youtube endpoints to main.py | `9f23c0e4` | `backend/main.py` |
| 3 | Add yt-dlp to requirements.txt | `7771e17e` | `backend/requirements.txt` |

## What Was Built

**Task 1 - Storage Service (`backend/services/storage.py`):**
- `VIDEO_DIR = /tmp/clipwise` constant
- `save_upload(file: UploadFile)` — saves uploaded file to `/tmp/clipwise/<uuid>/original.<ext>`, returns `{file_id, path, filename, duration}`
- `save_youtube(url: str)` — runs `yt-dlp --extract-audio --audio-format wav` and saves to `/tmp/clipwise/<uuid>/`, returns `{file_id, path, filename, duration}`
- `get_video_info(file_id: str)` — retrieves metadata by file_id
- In-memory `_video_metadata` dict tracking all stored files
- `_get_duration()` helper using ffprobe

**Task 2 - API Endpoints (`backend/main.py`):**
- Modified `/upload` to use `save_upload()` with proper error handling
- Added `/youtube` POST endpoint accepting `{url: str}` via `YouTubeRequest` model
- Added `/video/{file_id}/info` GET endpoint returning metadata
- Ensured `VIDEO_DIR` exists at app startup

**Task 3 - Dependencies:**
- Added `yt-dlp>=2024.0.0` to `backend/requirements.txt`
- Installed in backend virtual environment

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

| Check | Result |
|-------|--------|
| `from services.storage import ...` loads OK | ✅ |
| `from main import app` loads OK | ✅ |
| yt-dlp installed (v2026.03.17) | ✅ |
| 3 tasks completed | ✅ |
| 3 commits created | ✅ |

## Threat Flags

None identified.

## Self-Check

- [x] `backend/services/storage.py` exists with all functions
- [x] `backend/services/__init__.py` created
- [x] `backend/main.py` has /upload, /youtube, /video/{file_id}/info
- [x] yt-dlp in requirements.txt
- [x] All 3 commits present in git log