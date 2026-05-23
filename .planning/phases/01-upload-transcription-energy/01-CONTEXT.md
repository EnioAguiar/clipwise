# Phase 1: Upload + Transcription + Energy - Context

**Gathered:** 2025-05-23
**Status:** Ready for planning

## Phase Boundary

Accept video input (file upload or YouTube URL), transcribe audio locally with Faster Whisper, and extract audio energy using FFmpeg astats filter with Z-score normalization.

## Canonical References

### Project docs
- `.planning/REQUIREMENTS.md` — all 34 v1 requirements mapped to phases
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, and plan stubs

### Podcli reference
- `podcli/backend/services/audio_analyzer.py` — FFmpeg astats + Z-score implementation (primary reference)
- `podcli/backend/services/transcription.py` — Faster Whisper integration with segments/words output
- `podcli/backend/services/transcript_packer.py` — `pack_transcript` function that creates combined markdown with energy peaks

### Tech stack
- `frontend/` — Next.js 14 app (app router, Tailwind, shadcn/ui)
- `backend/main.py` — FastAPI entry point
- `backend/requirements.txt` — Python dependencies

## Implementation Decisions

### D-01: Video Input Methods
- **Both:** File upload (MP4, MKV, WAV) + YouTube URL
- YouTube: `yt-dlp` downloads audio to `/tmp/clipwise`, then processes

### D-02: UI Layout
- **Tabs:** Arquivo | YouTube
- Single box with toggle to switch between file dropzone and YouTube URL input
- NOT two separate components

### D-03: Processing Flow (Backend does everything)
- Frontend sends URL → Backend downloads (if YouTube) → Backend transcribes → Backend extracts energy
- All heavy lifting on backend (`yt-dlp` + Faster Whisper + FFmpeg)
- Frontend only receives results

### D-04: YouTube Download
- Download complete file first, then process (no streaming)
- File saved to `/tmp/clipwise/<unique_id>/`
- Backend handles everything via `yt-dlp`

### D-05: Whisper Model
- **`base`** model (~1GB RAM) — good balance of speed and accuracy

### D-06: Audio Energy Extraction
- FFmpeg `astats` filter per second + Z-score normalization (podcli-style)
- Algorithm: `z_avg * 0.4 + z_peak * 0.6` (peak weighted higher)
- Top 10% loudest moments = peaks

### D-07: Transcription Trigger
- **Manual button** ("Transcribe") — user clicks after upload/URL entry
- NOT automatic (avoids accidental long processing)

### D-08: Data Storage Format
- **Follow podcli pattern:**
  - `transcript.json` — full transcription with segments, words, speakers
  - `energy.json` — RMS energy per second from FFmpeg astats
  - `combined.md` — packed markdown for LLM reasoning (using `pack_transcript` logic)
- All saved in `/tmp/clipwise/<video_id>/`

### D-09: Configuration UI
- **Appears after processing** (not before)
- User sets: min/max clip duration, target clip count, output format, auto/manual mode
- Configuration visible in same page, but AFTER processing completes

### D-10: Progress Display
- **Everything on same page** (no navigation/wizard)
- Shows: progress bar with % + step list (e.g., "Downloading YouTube... 45%", "Transcribing... 67%")
- Both progress bar AND step list shown simultaneously

### D-11: Error Handling
- Log window showing each step as it happens
- If error: log shows what happened, with retry option
- Not toast notification — actual log window

## Existing Code Insights

### Reusable Assets
- `frontend/src/components/` — existing component structure
- `backend/services/` — services folder already exists (FastAPI structure)

### Integration Points
- `backend/main.py` — FastAPI entry point, add endpoints here
- `frontend/src/app/` — Next.js app router, add pages here

## Specific Ideas

- Follow podcli's `pack_transcript` pattern for combined output
- Use podcli's Z-score formula: `z_avg * 0.4 + z_peak * 0.6`
- Log window similar to podcli's progress display

## Deferred Ideas

None — discussion stayed within phase scope