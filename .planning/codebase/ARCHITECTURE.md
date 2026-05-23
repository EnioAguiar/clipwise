<!-- refreshed: 2026-05-23 -->
# Architecture

**Analysis Date:** 2026-05-23

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                      │
│              `frontend/src/app/page.tsx`                    │
├──────────────────┬──────────────────┬───────────────────────┤
│  ConfigPanel      │  MomentCard       │  WaveformVisualizer    │
│  `components/`    │  `components/`   │  `components/`        │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│                   `backend/main.py`                         │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  /upload     │  /youtube    │  /extract    │  /process      │
│  /video/*    │  /rank       │  /transcribe │  /opus/send    │
└──────────────┴──────────────┴──────────────┴────────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend Services Layer                     │
│              `backend/services/*.py`                        │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  storage     │  energy      │  transcription│  moment_ranker│
│  `storage`  │  `energy`    │  `transcrip.` │  `moment_rank. │
│              │  grok_client │               │  grok_client` │
└──────────────┴──────────────┴───────────────┴────────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│              External Services                              │
│     Groq API (LLM)  │  yt-dlp (YouTube)  │  Opus Clip API     │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Frontend SPA | Video upload/YT URL input, moment selection UI, video player | `frontend/src/app/page.tsx` |
| ConfigPanel | Processing config (min/max duration, target clips, format, mode) | `frontend/src/components/ConfigPanel.tsx` |
| MomentCard | Individual moment display and selection | `frontend/src/components/MomentCard.tsx` |
| WaveformVisualizer | Audio energy waveform display with peak markers | `frontend/src/components/WaveformVisualizer.tsx` |
| FastAPI App | HTTP API routing, CORS, request orchestration | `backend/main.py` |
| Storage Service | File upload save, YouTube download, metadata tracking | `backend/services/storage.py` |
| Energy Service | FFmpeg-based RMS extraction, peak detection, scoring | `backend/services/energy.py` |
| Transcription Service | Whisper-based audio transcription | `backend/services/transcription.py` |
| Moment Ranker | LLM + energy combined ranking, moment filtering | `backend/services/moment_ranker.py` |
| Grok Client | Groq API calls, prompt building, fallback ranking | `backend/services/grok_client.py` |

## Pattern Overview

**Overall:** REST API + SPA with chained processing pipeline

**Key Characteristics:**
- Single-page React frontend with Next.js app router
- FastAPI backend with synchronous processing chains
- Services layer isolates external tool integrations (FFmpeg, yt-dlp, Whisper, Groq)
- In-memory metadata store in `storage.py` (_video_metadata dict)
- File-based storage at `/tmp/clipwise/<video_id>/` for intermediate artifacts

## Layers

**Frontend (UI Layer):**
- Purpose: User interaction for video upload, configuration, moment browsing, export
- Location: `frontend/src/`
- Contains: React components, API client, UI primitives
- Depends on: Backend REST API at `localhost:8000`
- Used by: Browser users

**FastAPI Application (API Layer):**
- Purpose: HTTP endpoint routing, request validation, response formatting, CORS
- Location: `backend/main.py`
- Contains: Pydantic models, route handlers, middleware
- Depends on: Services layer, external APIs
- Used by: Frontend SPA

**Services Layer (Business Logic):**
- Purpose: Core processing logic — storage, energy analysis, transcription, moment ranking
- Location: `backend/services/`
- Contains: `storage.py`, `energy.py`, `transcription.py`, `moment_ranker.py`, `grok_client.py`
- Depends on: FFmpeg, yt-dlp, faster-whisper, Groq API
- Used by: `backend/main.py`

**Data/Artifact Storage:**
- Purpose: Persist intermediate and final artifacts
- Location: `/tmp/clipwise/<video_id>/` (transient temp storage)
- Contains: `transcript.json`, `energy.json`, `moments.json`, original video file
- Depends on: OS filesystem
- Used by: Services layer for cross-step data sharing

## Data Flow

### Primary Request Path (Upload → Process → Display)

1. **Upload** — `POST /upload` → `storage.save_upload()` (`backend/services/storage.py:20`)
2. **Extract** — `POST /extract` → chains transcription + energy extraction (`backend/main.py:222`)
3. **Process** — `POST /process` → `rank_moments()` → Groq API or fallback (`backend/services/moment_ranker.py:18`)
4. **Fetch Moments** — `GET /moments/{video_id}` → read from `moments.json` (`backend/main.py:349`)
5. **Fetch Video** — `GET /video/{file_id}` → `FileResponse` streaming (`backend/main.py:101`)
6. **Opus Export** — `POST /opus/send` → forward to Opus Clip API (`backend/main.py:371`)

### YouTube Download Path

1. **Download** — `POST /youtube` → `storage.save_youtube()` → yt-dlp (`backend/services/storage.py:60`)
2. **Continue** — Same extract/process flow as upload path

### Frontend Update Flow

1. `processVideo()` — upload or YouTube download → `POST /extract` → `POST /process` → `GET /moments/{video_id}` (`frontend/src/app/page.tsx:182`)
2. `rankMoments()` — trigger ranking with config → `POST /process` → `GET /moments/{video_id}` (`frontend/src/app/page.tsx:275`)
3. `sendToOpus()` — `POST /opus/send` with selected moments (`frontend/src/app/page.tsx:118`)

## Key Abstractions

**ProcessingConfig:**
- Purpose: Configuration parameters for clip extraction
- Examples: `backend/main.py:38` Pydantic model, `frontend/src/components/ConfigPanel.tsx:8` TypeScript interface
- Pattern: Shared between frontend and backend via manual duplication

**Moment:**
- Purpose: A ranked video clip candidate with scoring
- Examples: `backend/main.py:45` Pydantic model, `frontend/src/app/page.tsx:18` TypeScript interface
- Pattern: Created by Groq API, saved to `moments.json`, displayed in frontend

**Energy Profile:**
- Purpose: Audio energy analysis results
- Examples: `backend/services/energy.py:169` returns `{energy_data, segment_scores, mean_rms, peak_times}`
- Pattern: Extracted once, stored to `energy.json`, loaded by moment ranker

**Video Metadata:**
- Purpose: Track uploaded/downloaded video info in memory
- Examples: `backend/services/storage.py:17` `_video_metadata` dict
- Pattern: In-memory store keyed by `file_id` (not persisted across restarts)

## Entry Points

**Frontend SPA:**
- Location: `frontend/src/app/page.tsx`
- Triggers: User navigates to `http://localhost:3000`
- Responsibilities: All UI — file upload, YouTube URL, processing pipeline, moment display, Opus export

**Backend API:**
- Location: `backend/main.py`
- Triggers: Frontend fetch calls to `http://localhost:8000`
- Responsibilities: All server-side processing — file storage, transcription, energy, ranking, Opus forwarding

**Video Player:**
- Location: `frontend/src/app/page.tsx:479` `<video>` element
- Triggers: User clicks play on processed video
- Responsibilities: Stream playback via `GET /video/{video_id}`

## Architectural Constraints

- **Threading:** Single-threaded FastAPI/Uvicorn event loop. FFmpeg/subprocess calls are blocking but synchronous (no async subprocess)
- **Global state:** In-memory `_video_metadata` dict in `storage.py` — module-level singleton
- **Circular imports:** None detected
- **Persistence:** No database. Files stored at `/tmp/clipwise/` — transient, lost on restart
- **API key storage:** `.env` file read by `python-dotenv` at `backend/main.py:15`

## Anti-Patterns

### Shared Configuration Duplicated Across Frontend/Backend

**What happens:** `ProcessingConfig` exists as both a Pydantic model in `backend/main.py:38` and a TypeScript interface in `frontend/src/components/ConfigPanel.tsx:8`. No shared schema.

**Why it's wrong:** Changes to config structure require manual updates in both places. Drift causes runtime errors.

**Do this instead:** Define config schema in one place (e.g., a shared JSON schema or TypeScript types that the backend generates).

### In-Memory Metadata Store

**What happens:** `_video_metadata` dict in `backend/services/storage.py:17` stores file metadata in process memory.

**Why it's wrong:** Lost on server restart. No persistence. No scalability beyond single instance.

**Do this instead:** Use a proper database (SQLite, PostgreSQL) or at minimum persist metadata to disk.

### No Error Recovery for Chained Processing

**What happens:** If `/extract` partially succeeds (transcription succeeds, energy fails), the state is inconsistent. The next `/process` call will retry things but there's no idempotent design.

**Why it's wrong:** Partial failures leave the system in a broken state. Re-running can produce duplicate artifacts.

**Do this instead:** Use transactional or idempotent processing with explicit state flags per video artifact.

## Error Handling

**Strategy:** HTTPException propagation with status codes

**Patterns:**
- `HTTPException(status_code=404, detail="Video not found")` for missing resources (`backend/main.py:96`)
- `HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")` for internal errors (`backend/main.py:79`)
- Try/except around external API calls (Groq, Opus) with fallback or re-raise
- Frontend displays errors in red alert box: `frontend/src/app/page.tsx:391`

## Cross-Cutting Concerns

**Logging:** Python `logging` module via `logger.warning()`/`logger.error()` in `backend/main.py`. Frontend uses custom `addLog()` callback with timestamped entries displayed in log window UI.

**Validation:** Pydantic `BaseModel` for all request/response bodies in FastAPI. TypeScript interfaces for frontend props.

**Authentication:** None currently implemented. CORS restricted to `http://localhost:3000` in `backend/main.py:21`.

**CORS:** Configured for `http://localhost:3000` only in `backend/main.py:19-25`.

---

*Architecture analysis: 2026-05-23*