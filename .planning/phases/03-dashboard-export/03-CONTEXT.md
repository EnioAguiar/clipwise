# Phase 3: Dashboard + Export - Context

**Gathered:** 2025-05-23
**Status:** Ready for planning

## Phase Boundary

Display ranked moments in UI with video player at timestamp, allow filtering/selection, export timestamps manually, and send to Opus Clip API.

## Canonical References

### Project docs
- `.planning/REQUIREMENTS.md` — Phase 3 requirements (DASH-01 to DASH-06, EXPT-01, EXPT-02)
- `.planning/ROADMAP.md` — Phase 3 goal and success criteria
- `.planning/phases/01-upload-transcription-energy/01-CONTEXT.md` — Phase 1 decisions
- `.planning/phases/02-moment-detection-engine/02-CONTEXT.md` — Phase 2 decisions

### Tech stack
- `frontend/src/app/page.tsx` — existing page (simulated processing)
- `frontend/src/components/ConfigPanel.tsx` — Phase 1 config UI
- `backend/main.py` — FastAPI with all endpoints
- `backend/services/moment_ranker.py` — Phase 2 moment ranking
- `backend/services/storage.py` — Phase 1 storage

## Implementation Decisions

### D-01: Dashboard UI
- **Lista de cards** — Each moment is a card with:
  - Rank/order number
  - Start/end timestamps
  - Duration
  - Energy score
  - Transcript snippet preview
  - Content type badge (guest_story, technical_insight, etc.)
  - Total score (from Grok or energy fallback)

### D-02: Video Player
- **HTML5 video tag** — works for local files and direct video
- For YouTube: video is downloaded locally, then played via HTML5
- Video player positioned at top or side of moments list
- Clicking a moment jumps video to that timestamp

### D-03: Moment Selection
- **Checkbox per card** — user can select/deselect individual moments
- **Slider for top N** — slider at top to automatically select top N moments (3-20)
- **Global button** — "Enviar pro Opus" button at bottom (enabled when 1+ selected)
- **Individual copy** — per-card "Copiar timestamp" button

### D-04: Export Options
All 3 available:
- **Copiar timestamps** — format for Opus Clip API: `[start]-[end]` per line
- **Enviar pro Opus Clip API** — sends selected moments directly to Opus Clip API
- **Exportar JSON** — downloads `moments.json` with all moment data

### D-05: Frontend-Backend Integration
- Connect simulated `simulateProcessing` to real backend endpoints:
  - POST /upload → file upload
  - POST /youtube → YouTube download
  - POST /transcribe → triggers transcription (need to add this endpoint to main.py)
  - POST /energy → triggers energy extraction
  - POST /rank → moment ranking with Grok
- All processing happens on backend
- Frontend polls or receives results via JSON

### D-06: Backend Endpoints Needed
Add to backend/main.py:
- POST /transcribe — accepts {video_id} or {file_id}, calls transcription.py
- POST /process — chains upload → transcribe → energy → rank in one call

### D-07: State Management
- Frontend states: idle → uploading → transcribing → analyzing → ranking → complete
- Store results in localStorage for config persistence
- Moments data kept in memory or localStorage for session

## Existing Code Insights

### Integration Points
- `frontend/src/app/page.tsx` — replace simulateProcessing with real API calls
- `backend/main.py` — add /transcribe and /process endpoints
- `backend/services/transcription.py` — already exists, just needs endpoint wrapper
- `backend/services/moment_ranker.py` — already exists, needs /rank endpoint

### Phase 1 UI already has
- Arquivo/YouTube tabs
- Upload dropzone
- Manual "Transcrever" button (but fake — needs real backend call)
- Progress bar + step list
- Log window
- ConfigPanel (shows after processing)

### Phase 2 endpoints already have
- POST /rank — moment ranking with Grok fallback
- All data saved in /tmp/clipwise/<video_id>/

## Specific Ideas

- Video player at top of page, moments list below
- Click moment card → video jumps to timestamp + plays preview
- Color-coded scores (high=green, medium=yellow, low=red)
- "Top 10 momentos" slider default at 10
- Copy button shows toast "Copiado!" on success
- Opus API error shows in log window with retry option

## Deferred Ideas

None — discussion stayed within phase scope