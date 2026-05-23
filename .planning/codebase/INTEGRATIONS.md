# External Integrations

**Analysis Date:** 2026-05-23

## APIs & External Services

**Transcription:**
- OpenAI Whisper - Speech-to-text via `openai-whisper` and `faster-whisper`
  - SDK/Client: `openai-whisper` (Python), `faster-whisper` (Python)
  - Auth: `OPENAI_API_KEY` (optional, uses CPU fallback if not set)
  - Config: `WHISPER_MODEL`, `CUDA_DEVICE`

**AI/LLM:**
- Groq - Moment ranking via LLM
  - SDK/Client: `groq` Python package
  - Auth: `GROQ_API_KEY`
  - Endpoint: `https://api.groq.com/v1/` (inferred from `groq>=3.0.0`)

**Video Processing:**
- Opus Clip API - Send moments for automated clip creation
  - SDK/Client: Raw HTTP via `httpx.AsyncClient`
  - Auth: `OPUS_API_KEY`
  - Endpoint: `https://api.opus.clip/v1/clips`
  - Usage: `POST /opus/send` in `backend/main.py`

**YouTube:**
- yt-dlp - Download YouTube videos/audio
  - SDK/Client: `yt-dlp>=2024.0.0`
  - Auth: None (public videos)
  - Usage: `POST /youtube` endpoint

## Data Storage

**Databases:**
- None (no database detected)
  - Storage approach: File-based via `/tmp/clipwise/<uuid>/` directories
  - Metadata stored as JSON files

**File Storage:**
- Local filesystem (`/tmp/clipwise/`) - Video uploads, transcripts, energy data, moments
- Persistent output: `.podcli/output/` for rendered clips

**Caching:**
- Transcription cache: `.podcli/cache/` directory
- Transcript caching via `transcript-cache.ts`

## Authentication & Identity

**Auth Provider:**
- None (no auth system detected)
  - API runs with CORS open to `http://localhost:3000`

## Monitoring & Observability

**Error Tracking:**
- None detected

**Logs:**
- Winston 3.17.0 - Structured logging in podcli
- Python `logging` (uvicorn) - Backend API logs
- Console warnings used for request tracing in `backend/main.py`

## CI/CD & Deployment

**Hosting:**
- Not detected (no deployment configuration found)

**CI Pipeline:**
- GitHub Actions (`.github/workflows/ci.yml`)
  - Node.js 20: TypeScript build + typecheck + vitest tests
  - Python 3.12: pytest (minimal deps, no whisper/torch)

## Environment Configuration

**Required env vars:**
- `OPENAI_API_KEY` - OpenAI (Whisper)
- `OPUS_API_KEY` - Opus Clip API
- `GROQ_API_KEY` - Groq LLM (inferred from groq usage)
- `FFMPEG_PATH` - FFmpeg binary path (defaults to "ffmpeg")
- `WHISPER_MODEL` - Whisper model size (optional)
- `CUDA_DEVICE` - CUDA GPU index (optional)

**Secrets location:**
- `.env` file in `backend/` directory
- `.env.example` files present (not committed with secrets)

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- `POST /opus/send` - Sends timestamps + video to Opus Clip API
  - Payload: `{video_url, timestamps}`
  - Auth: Bearer token

---

*Integration audit: 2026-05-23*