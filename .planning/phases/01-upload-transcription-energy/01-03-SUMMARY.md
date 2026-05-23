---
phase: 01-upload-transcription-energy
plan: 03
subsystem: api
tags: [ffmpeg, audio-analysis, z-score, fastapi]

# Dependency graph
requires:
  - phase: 01-upload-transcription-energy
    provides: Video file storage and file_id system
provides:
  - FFmpeg astats RMS extraction per second
  - Z-score normalization with z_avg * 0.4 + z_peak * 0.6 formula
  - Top 10% peak moments identification
  - /energy endpoint returning {file_id, energy_path, peak_times, mean_rms, segment_scores}
affects:
  - Phase 2 (Analysis Engine)
  - Phase 3 (Dashboard + Export)

# Tech tracking
tech-stack:
  added: [ffmpeg astats filter, ebur128 fallback]
  patterns: [Z-score normalization, energy profile pipeline]

key-files:
  created:
    - backend/services/energy.py
  modified:
    - backend/main.py

key-decisions:
  - "FFmpeg astats filter for RMS extraction (follows podcli pattern)"
  - "Z-score formula: z_avg * 0.4 + z_peak * 0.6 (peak weighted higher)"
  - "Top 10% loudest moments identified as peaks"
  - "Fallback to ebur128 filter if astats returns no data"

patterns-established:
  - "Energy data saved to /tmp/clipwise/<video_id>/energy.json"
  - "segment_scores computed per segment using Z-score normalization"

requirements-completed: [ENERG-01, ENERG-02, ENERG-03]

# Metrics
duration: 3min
completed: 2026-05-23
---

# Phase 1: Upload + Transcription + Energy Summary

**FFmpeg astats RMS extraction with Z-score normalization for peak moment detection**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-23T17:23:53Z
- **Completed:** 2026-05-23T17:26:33Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created `backend/services/energy.py` with FFmpeg astats extraction
- Added `POST /energy` endpoint to `backend/main.py`
- Implemented Z-score normalization formula (z_avg * 0.4 + z_peak * 0.6)
- Energy data saved to `/tmp/clipwise/<video_id>/energy.json`

## task Commits

Each task was committed atomically:

1. **task 1: Create backend/services/energy.py with FFmpeg astats extraction** - `9ac2e6e1` (feat)
2. **task 2: Add /energy endpoint to main.py** - `b6dd53c9` (feat)

**Plan metadata:** `b6dd53c9` (docs: complete plan)

## Files Created/Modified
- `backend/services/energy.py` - Audio energy extraction with FFmpeg astats, Z-score normalization, peak detection
- `backend/main.py` - Added EnergyRequest model and POST /energy endpoint

## Decisions Made
- Followed podcli audio_analyzer.py patterns exactly
- Used FFmpeg astats filter for RMS extraction per second
- Implemented Z-score normalization with z_avg * 0.4 + z_peak * 0.6 formula
- Top 10% loudest moments identified as peaks
- Fallback to ebur128 filter if astats returns no data

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Energy extraction complete and ready for Phase 2 (Analysis Engine)
- /energy endpoint accepts {file_id, segments?} and returns energy profile
- No blockers

---
*Phase: 01-upload-transcription-energy*
*Completed: 2026-05-23*