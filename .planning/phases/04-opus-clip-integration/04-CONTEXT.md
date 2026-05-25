# Phase 4: Opus Clip Integration - Context

**Gathered:** 2026-05-25
**Status:** Ready for planning

## Phase Boundary

Send selected moments to Opus Clip API and download generated clips automatically.

## Canonical References

### Project docs
- `.planning/REQUIREMENTS.md` — Phase 4 requirements (OPUS-01 to OPUS-05)
- `.planning/ROADMAP.md` — Phase 4 goal and success criteria
- `.planning/phases/01-upload-transcription-energy/01-CONTEXT.md` — Phase 1 decisions
- `.planning/phases/02-moment-detection-engine/02-CONTEXT.md` — Phase 2 decisions
- `.planning/phases/03-dashboard-export/03-CONTEXT.md` — Phase 3 decisions

### Opus Clip API Docs
- `https://help.opus.pro/api-reference/endpoints/upload-video-create-project` — Full upload flow (4 steps)
- `https://help.opus.pro/api-reference/overview` — API overview and authentication

### Tech stack
- `frontend/src/app/page.tsx` — existing page with moments list
- `frontend/src/components/MomentCard.tsx` — existing moment card component
- `backend/main.py` — FastAPI with existing `/opus/send` stub

## Implementation Decisions

### D-01: Workflow Order
- **Video upload first, then timestamps**
- User processes video → sees highlights → uploads video to Opus → then sends timestamps
- This is the correct order: Opus needs the video before it can create clips at specific timestamps

### D-02: Upload Video Button
- **Separate button** "Subir vídeo para Opus" (not automatic)
- Button appears in highlights section after moments are ranked
- When clicked: shows progress (upload pode demorar)
- After success: enables the timestamp "portões" (gates)

### D-03: Timestamp Verification Pop-up
- **Pop-up window** to verify each timestamp before sending
- Shows video at that timestamp for visual verification
- User confirms: "Está certo" → sends to Opus
- This is manual per-moment check before sending

### D-04: Send Options
Two options for sending timestamps:
- **Individual**: Click each moment's button to send one by one
- **Send all**: Button to send all moments at once (no verification)

### D-05: Opus API Flow
Full upload flow required:
```
1. POST /api/upload-links → get uploadId + url
2. POST <url> with x-goog-resumable: start → get location
3. PUT <location> with video file → upload complete
4. POST /api/clip-projects with uploadId + timestamps
```

### D-06: YouTube videos
- If video came from YouTube URL, it already has a public URL
- Can skip upload step and send timestamps directly
- Check: if video source is YouTube, use direct URL

### D-07: Clip Download
- **NOT implemented** in ClipWise
- User downloads and manages clips on Opus website directly
- This aligns with "resto eu faco tudo pelo site do opus"

## Existing Code Insights

### Integration Points
- `frontend/src/app/page.tsx` — moments display with "Enviar pro Opus" button (needs update)
- `backend/main.py` — existing `/opus/send` stub (needs complete rewrite)
- `.planning/codebase/STACK.md` — httpx already available for async HTTP

### Reusable Assets
- `backend/services/storage.py` — video storage path: `/tmp/clipwise/<video_id>/`
- `frontend/src/components/MomentCard.tsx` — existing card component for moment display

## Specific Ideas

- Use browser's native fetch with resumable upload progress tracking
- Show progress bar during video upload (can be slow for large files)
- Pop-up could be a modal overlaying the video player
- YouTube URL detection to skip upload step

## Deferred Ideas

None — discussion stayed within phase scope