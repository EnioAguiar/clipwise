# Technology Stack

**Analysis Date:** 2026-05-23

## Languages

**Primary:**
- TypeScript 5.7.0 - podcli MCP server, web UI, Remotion video rendering
- Python 3.12 - Backend API (FastAPI), video processing services, Whisper transcription
- JavaScript - Legacy podcli CLI entry point (`podcli` executable)

**Secondary:**
- CSS - Tailwind CSS styling in frontend

## Runtime

**Environment:**
- Node.js >=18.0.0 (podcli), Node.js 20 (CI)
- Python 3.12

**Package Manager:**
- npm 10.x (podcli, frontend)
- pip (backend Python dependencies)
- Lockfile: `package-lock.json` present in podcli and frontend

## Frameworks

**Core:**
- Express 4.21.0 - Web server for podcli UI (`src/ui/web-server.ts`)
- FastAPI 0.111.0 - Backend REST API (`backend/main.py`)
- Next.js 14.2.0 - Frontend React framework (`frontend/`)

**Video Processing:**
- Remotion 4.0.441 - Video rendering (titles, clips with captions)
- FFmpeg - External video processing (invoked via CLI)
- faster-whisper 1.0.0 - Speech-to-text transcription

**AI/ML:**
- OpenAI Whisper - Transcription (Python)
- Groq - LLM moment ranking (`backend/services/grok_client.py`)
- OpenAI - General AI integration

**MCP (Model Context Protocol):**
- @modelcontextprotocol/sdk 1.12.1 - MCP server implementation

**UI Components:**
- Radix UI - Headless React components (slider, checkbox, select)
- Lucide React - Icons
- class-variance-authority - Tailwind variant utilities

**Testing:**
- Vitest 2.1.9 - TypeScript unit tests
- pytest - Python unit tests

**Build/Dev:**
- TypeScript 5.7.0 - Type checking and compilation
- tsx 4.19.0 - TypeScript execution for dev
- Tailwind CSS 3.4.0 - CSS framework

## Key Dependencies

**Critical:**
- `faster-whisper` 1.0.0 - CPU-efficient Whisper transcription
- `openai-whisper` >=20231117 - Alternative Whisper integration
- `remotion` 4.0.441 - Video rendering with React
- `groq` 3.0.0 - LLM API client for moment ranking
- `yt-dlp` 2024.0.0 - YouTube video downloading

**Infrastructure:**
- `express` 4.21.0 - HTTP server
- `fastapi` 0.111.0 - Python REST API
- `uvicorn` 0.29.0 - ASGI server for FastAPI
- `winston` 3.17.0 - Logging (podcli)

**Storage:**
- `multer` 1.4.5-lts.1 - File upload handling

## Configuration

**Environment:**
- `.env` files present (backend, podcli)
- `dotenv` 16.4.7 - Environment variable loading
- Key configs: `OPENAI_API_KEY`, `OPUS_API_KEY`, `WHISPER_MODEL`, `CUDA_DEVICE`

**Build:**
- `tsconfig.json` - TypeScript config (ES2022 target, ESNext module)
- `next.config.js` - Next.js configuration
- `tailwind.config.ts` - Tailwind CSS config
- `remotion.config.ts` - Remotion configuration

## Platform Requirements

**Development:**
- Node.js >=18.0.0
- Python 3.12
- FFmpeg CLI (external binary, path configured via `FFMPEG_PATH`)

**Production:**
- Node.js runtime for podcli
- Python runtime for backend API
- FFmpeg available on system PATH

---

*Stack analysis: 2026-05-23*