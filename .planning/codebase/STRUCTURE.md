# Codebase Structure

**Analysis Date:** 2026-05-23

## Directory Layout

```
/home/enio/clipwise/
├── backend/                  # FastAPI Python backend
│   ├── main.py              # FastAPI app, routes, request handlers
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables (API keys)
│   ├── .env.example         # Example env vars
│   ├── services/           # Business logic services
│   │   ├── __init__.py
│   │   ├── storage.py       # File upload, YouTube download, metadata
│   │   ├── energy.py        # FFmpeg RMS extraction, peak detection
│   │   ├── transcription.py # Whisper transcription
│   │   ├── moment_ranker.py # Moment ranking orchestration
│   │   └── grok_client.py   # Groq API client
│   ├── tests/              # Backend tests (empty/subdir)
│   └── venv/               # Python virtual environment
├── frontend/               # Next.js React frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx     # Main SPA page
│   │   │   ├── layout.tsx   # Root layout
│   │   │   └── globals.css  # Global styles
│   │   ├── components/
│   │   │   ├── ConfigPanel.tsx
│   │   │   ├── MomentCard.tsx
│   │   │   ├── WaveformVisualizer.tsx
│   │   │   └── ui/
│   │   │       ├── button.tsx
│   │   │       └── slider.tsx
│   │   └── lib/
│   │       └── utils.ts     # cn(), formatTime(), formatTimestamp()
│   ├── package.json
│   └── .next/               # Next.js build output (generated)
├── podcli/                  # CLI tool (per repo name)
├── .planning/              # GSD planning artifacts
│   └── codebase/           # Codebase map documents
├── .gitignore
└── README.md
```

## Directory Purposes

**Backend (`backend/`):**
- Purpose: FastAPI REST API server
- Contains: `main.py` (app/routes), `services/` (business logic), `requirements.txt`
- Key files: `backend/main.py`, `backend/services/storage.py`

**Frontend (`frontend/`):**
- Purpose: Next.js single-page application
- Contains: `src/app/` (pages), `src/components/` (React components), `src/lib/` (utilities)
- Key files: `frontend/src/app/page.tsx`, `frontend/src/components/ConfigPanel.tsx`

**Services (`backend/services/`):**
- Purpose: Isolated business logic for each processing step
- Contains: `storage.py`, `energy.py`, `transcription.py`, `moment_ranker.py`, `grok_client.py`
- Key files: `backend/services/storage.py`, `backend/services/energy.py`

**UI Components (`frontend/src/components/ui/`):**
- Purpose: Primitive UI components (button, slider)
- Contains: Reusable Shadcn-style components
- Key files: `frontend/src/components/ui/button.tsx`

**Planning (`.planning/`):**
- Purpose: GSD workflow artifacts — roadmap, phases, codebase maps
- Contains: `codebase/` (this analysis), `graphs/`, `learnings/`, milestone docs
- Generated: Yes

## Key File Locations

**Entry Points:**

- **Backend:** `backend/main.py` — run with `uvicorn main:app`
- **Frontend:** `frontend/src/app/page.tsx` — run with `next dev` in `frontend/`
- **Frontend API Client:** `frontend/src/app/page.tsx:44` — `const API_BASE = 'http://localhost:8000'`

**Configuration:**

- **Python deps:** `backend/requirements.txt`
- **Node deps:** `frontend/package.json`
- **Env vars:** `backend/.env` (local), `backend/.env.example` (template)
- **API Base URL:** `frontend/src/app/page.tsx:44` hardcoded to `http://localhost:8000`

**Core Logic:**

- **Video upload:** `backend/services/storage.py:20` `save_upload()`
- **YouTube download:** `backend/services/storage.py:60` `save_youtube()`
- **Energy extraction:** `backend/services/energy.py:169` `get_energy_profile()`
- **Transcription:** `backend/services/transcription.py` `transcribe_file()`
- **Moment ranking:** `backend/services/moment_ranker.py:18` `rank_moments()`
- **LLM client:** `backend/services/grok_client.py:16` `call_grok_moment_selection()`

**API Routes (in `backend/main.py`):**

- `POST /upload` (line 67)
- `POST /youtube` (line 82)
- `GET /video/{file_id}` (line 101)
- `POST /extract` (line 222)
- `POST /process` (line 276)
- `GET /moments/{video_id}` (line 349)
- `POST /opus/send` (line 371)
- `GET /energy/{video_id}` (line 420)

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g., `moment_ranker.py`, `grok_client.py`)
- TypeScript/TSX: `PascalCase.tsx` for components, `camelCase.ts` for utilities (e.g., `ConfigPanel.tsx`, `utils.ts`)
- Directories: `snake_case/` for Python services, `camelCase/` for frontend components

**Functions:**
- Python: `snake_case` (e.g., `save_upload`, `get_energy_profile`, `call_grok_moment_selection`)
- TypeScript: `camelCase` in React components (e.g., `processVideo`, `rankMoments`, `sendToOpus`)

**Variables:**
- Python: `snake_case` (e.g., `video_id`, `energy_data`, `peak_times`)
- TypeScript: `camelCase` (e.g., `videoId`, `energyData`, `processingState`)
- React state: `camelCase` with descriptive suffixes (e.g., `processingState`, `selectedMoments`, `opusStatus`)

**Types/Classes:**
- Python: `PascalCase` for Pydantic models (e.g., `ProcessingConfig`, `EnergyRequest`, `Moment`)
- TypeScript: `PascalCase` for interfaces and types (e.g., `ProcessingConfig`, `Moment`, `EnergyPoint`)
- React components: `PascalCase` (e.g., `ConfigPanel`, `MomentCard`, `WaveformVisualizer`)

## Where to Add New Code

**New API Endpoint:**
- Location: `backend/main.py` — add new route function, import service if needed
- Request model: Pydantic `BaseModel` class for validation
- Response model: Pydantic `BaseModel` or built-in type

**New Service Module:**
- Location: `backend/services/new_service.py`
- Follow pattern: `def save_X()` returns dict with metadata, pure functions preferred
- Import in `main.py` as `from services.new_service import func`

**New Frontend Component:**
- Location: `frontend/src/components/NewComponent.tsx`
- Use `'use client'` directive for client-side interactivity
- Import utility from `@/lib/utils` for `cn()` class merging

**New UI Primitive:**
- Location: `frontend/src/components/ui/` — add to existing or create new primitive

**Processing Config Change:**
- Update both: `backend/main.py:38` `ProcessingConfig` Pydantic model AND `frontend/src/components/ConfigPanel.tsx:8` `ProcessingConfig` TypeScript interface

**External API Integration:**
- Location: `backend/services/new_api_client.py`
- Follow pattern of `grok_client.py`: functions for API calls, error handling, fallback

## Special Directories

**`backend/venv/`:**
- Purpose: Python virtual environment
- Generated: Yes (by `python -m venv`)
- Committed: No (in `.gitignore`)

**`frontend/.next/`:**
- Purpose: Next.js build cache and output
- Generated: Yes (by `next build`)
- Committed: No (in `.gitignore`)

**`/tmp/clipwise/`:**
- Purpose: Transient file storage for uploaded videos, transcripts, energy data, moments
- Generated: Yes (created at runtime by services)
- Committed: No (in `.gitignore`, OS-level temp)

**`frontend/node_modules/`:**
- Purpose: NPM packages
- Generated: Yes (by `npm install`)
- Committed: No (in `.gitignore`)

**`.planning/`:**
- Purpose: GSD workflow state, roadmap, phase plans, codebase maps
- Generated: Yes (by GSD commands)
- Committed: Yes (version controlled planning artifacts)

---

*Structure analysis: 2026-05-23*