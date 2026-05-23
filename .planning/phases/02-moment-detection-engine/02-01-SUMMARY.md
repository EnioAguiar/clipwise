---
phase: 02-moment-detection-engine
plan: 01
subsystem: api
tags: [grok, xai, moment-ranking, energy-analysis, transcript]

# Dependency graph
requires:
  - phase: 01-upload-transcription-energy
    provides: transcript.json, energy.json, /tmp/clipwise/<video_id>/ structure
provides:
  - Grok AI client (call_grok_moment_selection, fallback_energy_ranking)
  - Moment ranking service (rank_moments, save_moments)
  - POST /rank endpoint for ranked moments
affects:
  - phase-3-dashboard-export (needs /rank endpoint for moment display)
  - phase-4-opus-clip-integration (needs moments.json for clip generation)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Grok API integration with structured JSON prompt
    - Energy-only fallback when LLM unavailable
    - Overlap removal via sorted-by-score greedy algorithm
    - segments array for tight cuts around filler

key-files:
  created:
    - backend/services/grok_client.py
    - backend/services/moment_ranker.py
  modified:
    - backend/main.py

key-decisions:
  - "Grok API key read at runtime from GROK_API_KEY env var"
  - "Fallback to energy-only ranking when API fails or use_llm=false"
  - "Overlap resolution: higher-scored moment wins"

patterns-established:
  - "Prompt format follows D-03: hook/standalone/relevance/quotability scoring (1-5 each)"
  - "Output format follows D-04: start, end, duration, total_score, scores, transcript_snippet, segments, content_type"

requirements-completed: [ENERG-04, MOMENT-01, MOMENT-02, MOMENT-03, MOMENT-04]

# Metrics
duration: ~3min
completed: 2026-05-23
---

# Phase 2 Plan 1: Moment Detection Engine Summary

**Grok AI-powered moment ranking combining audio energy + transcript timestamps, returning top N clips with hook/standalone/relevance/quotability scores**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-05-23T17:28:00Z
- **Completed:** 2026-05-23T17:31:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Grok API client with structured moment selection prompt (D-03 criteria)
- Energy-only fallback when API unavailable
- POST /rank endpoint returning D-04 format moments

## task Commits

Each task was committed atomically:

1. **task 1: Create Grok API client module** - `7dbcdd35` (feat)
2. **task 2: Create moment ranker service** - `024db950` (feat)
3. **task 3: Add /rank endpoint to main.py** - `c67886ad` (feat)

## Files Created/Modified
- `backend/services/grok_client.py` - Grok API calls with transcript + energy input, fallback to energy-only
- `backend/services/moment_ranker.py` - Main moment ranking logic, loads transcript + energy, filters overlaps
- `backend/main.py` - POST /rank endpoint accepting video_id + config

## Decisions Made
- Used urllib.request instead of httpx (already in requirements.txt but using stdlib for simplicity)
- Removed unused transcription import in moment_ranker.py (faster-whisper not needed at ranking time)
- Renamed ProcessingConfig fields: min_duration→min_clip_duration, max_duration→max_clip_duration

## Deviations from Plan

**1. [Rule 3 - Blocking] Removed unused transcription import**
- **Found during:** task 2 (moment_ranker.py creation)
- **Issue:** `from .transcription import transcribe_file` caused ModuleNotFoundError for faster_whisper in test
- **Fix:** Removed the import — transcription is done in Phase 1, moment_ranker only needs transcript.json on disk
- **Files modified:** backend/services/moment_ranker.py
- **Verification:** Module imports cleanly
- **Committed in:** 024db950 (task 2 commit)

---

**Total deviations:** 1 auto-fixed (blocking)
**Impact on plan:** Deviation prevented test failure. No scope change.

## Issues Encountered
- None - all three tasks executed as planned

## User Setup Required
**GROK_API_KEY environment variable required for LLM mode.** If not set, the system automatically falls back to energy-only ranking.

## Next Phase Readiness
- /rank endpoint ready for Phase 3 dashboard integration
- moments.json output format compatible with D-04 specification
- Grok API or energy-only fallback operational

---
*Phase: 02-moment-detection-engine*
*Completed: 2026-05-23*