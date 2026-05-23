---
phase: "03"
plan: "03"
subsystem: dashboard-export
tags: [opus-clip, export, api-integration]
dependency_graph:
  requires:
    - "03-01"
    - "03-02"
  provides:
    - "POST /opus/send endpoint"
    - "GET /energy/{video_id} endpoint"
    - "sendToOpus() frontend function"
  affects:
    - backend/main.py
    - frontend/src/app/page.tsx
tech_stack:
  added:
    - httpx (async HTTP client for Opus API calls)
  patterns:
    - FastAPI endpoint with external API call
    - React useState for async operation feedback
    - Loading/success/error state machine
key_files:
  created: []
  modified:
    - backend/main.py (added /opus/send and /energy/{video_id} endpoints)
    - frontend/src/app/page.tsx (added sendToOpus function and opusStatus state)
decisions:
  - "Used httpx.AsyncClient for async Opus API calls (而非同步requests)"
  - "Reset opusStatus when processing new video to avoid stale state"
  - "Opus API errors surface in both error div and log window for visibility"
metrics:
  duration_seconds: ~60
  completed_date: "2026-05-23T18:31:13Z"
  tasks_completed: 2
  files_modified: 2
---

# Phase 03 Plan 03: Opus Clip Integration Summary

**Opus Clip API integration — send selected moments with one click, show feedback, handle errors gracefully.**

## What Was Built

- **POST /opus/send endpoint** — receives `{video_id, moments: [{start, end}, ...]}`, calls Opus Clip API at `https://api.opus.clip/v1/clips`, returns `{status, job_id, moments_count}`
- **GET /energy/{video_id} endpoint** — returns energy data from `/tmp/clipwise/{video_id}/energy.json` for waveform visualization
- **sendToOpus() frontend function** — POSTs selected moments to backend, manages `opusStatus` state machine (`idle` → `sending` → `success`|`error`)
- **"Enviar pro Opus" button** — disabled when nothing selected or already sending, shows spinner during upload, disabled during flight

## Commits

| Commit | Description |
|--------|-------------|
| `2a564105` | feat(03-03): add POST /opus/send and GET /energy/{video_id} endpoints |
| `06cc7c8e` | feat(03-03): wire Enviar pro Opus button with state feedback |

## Verification

- Backend `/opus/send` returns `job_id` from Opus API response
- Backend `/energy/{video_id}` returns `energy_data` and `peak_times` for visualization
- Frontend button shows loading spinner while `opusStatus === 'sending'`
- Success displays job_id and moment count
- Error displays error message with API guidance

## Deviations from Plan

None — plan executed exactly as written.

## Threat Flags

None — new endpoints are internal API routes, no new attack surface introduced.