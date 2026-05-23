# ClipWise

## What This Is

ClipWise is a local system that analyzes live streams (Twitch, YouTube, etc.) to detect and extract the best moments automatically using audio energy analysis + optional LLM ranking, then sends timestamps to Opus Clip API for clip generation — all running locally via venv.

## Core Value

Automatically find the best moments in a 1-hour live stream and generate publishable short clips with minimal credit waste.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Upload live stream (MP4, MKV, WAV, YouTube link)
- [ ] Transcribe audio using Faster Whisper (local, no API cost)
- [ ] Extract audio energy per second using FFmpeg astats (RMS levels)
- [ ] Z-score normalization to identify energy peaks (risos, aplausos, ênfase)
- [ ] Combine energy peaks + transcript to rank moments
- [ ] Configure min/max clip duration (podcli-style: default 30s-60s)
- [ ] Configure target number of clips (slider 3-20, default 10)
- [ ] Dashboard showing ranked moments with video player at timestamp
- [ ] Export timestamps manually (copy/paste to Opus)
- [ ] Generate clips automatically via Opus Clip API

### Out of Scope

- Cloud hosting / multi-user — local venv only
- Persistent history — JSON is transient, not stored long-term
- Direct video editing — timestamps only, actual clip generation via Opus API
- Pyannote/speaker diarization — not needed for timestamp detection
- Multi-segment cutting — Opus handles the clip rendering

## Context

**Existing work:** Scaffold created with Next.js frontend and FastAPI backend. Frontend runs at localhost:3000, backend at localhost:8000.

**Reference: podcli approach**
- Audio energy: FFmpeg `astats` filter → RMS per second → Z-score normalization
- Score: `z_avg * 0.4 + z_peak * 0.6` (peak weighted higher)
- Clip duration: MIN=20s, TARGET=30-45s, MAX=60s (viral sweet spot)

**Tech stack decisions:**
- Frontend: Next.js 14 (App Router) + Tailwind + shadcn/ui
- Backend: FastAPI (Python) in local venv
- Transcription: Faster Whisper (local, free)
- Audio analysis: FFmpeg astats (free)
- LLM analysis: Optional deferral (future decision)
- Integration: Opus Clip REST API

**Credit economy:**
- Opus: 1 credit = 1 minute of video
- Minimum clip: 1 credit (even for 30s clips)
- Strategy: Find the best moments → spend credits only on what matters

## Constraints

- **Local only**: venv environment, no cloud — `npm run dev` / `uvicorn main:app`
- **Budget-conscious**: Minimize Opus credits by pre-filtering moments
- **Credit economy**: 1 credit = 1 minute; clip duration can be shorter than 1 min but costs 1 credit minimum

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Local venv, not cloud | Cost control, privacy | — Pending |
| Next.js frontend | Robust, scalable UI | — Pending |
| Faster Whisper (local) | Free transcription vs OpenAI API cost | — Pending |
| FFmpeg audio energy | Detect peaks (risos, aplausos) like podcli | — Pending |
| Z-score normalization | Adapt to audio baseline, find real peaks | — Pending |
| Config: 30s min / 60s max | Podcli viral sweet spot for short-form | — Pending |
| Opus Clip API | Generate clips at timestamps | — Pending |
| No speaker diarization | Not needed for timestamp detection | — Pending |
| LLM deferred | Audio energy sufficient for v1; AI later | — Pending |

---

*Last updated: 2025-05-22 after adding audio energy analysis (podcli-style)*