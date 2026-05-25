# Phase 4: Opus Clip Integration - Discussion Log

**Date:** 2026-05-25
**Phase:** 04-opus-clip-integration

## Discussion Summary

User explained the desired workflow clearly:
1. Process video → see highlights
2. "Subir vídeo para Opus" button uploads video to Opus first
3. After upload success, timestamp "portões" are enabled
4. Each timestamp has a button with pop-up to verify visually
5. User confirms each timestamp before sending (or "send all")
6. Video first, then timestamps
7. Everything else (download, edit) done on Opus website

## Decisions Made

| Area | Decision |
|------|----------|
| Workflow order | Video upload first, then timestamps |
| Upload trigger | Separate button "Subir vídeo para Opus" |
| Verification | Pop-up for each timestamp before sending |
| Send options | Individual (one by one) or "send all" |
| YouTube handling | Skip upload, use direct URL |
| Download clips | NOT implemented — user does on Opus site |

## Gray Areas Resolved

All gray areas resolved through user's clear workflow explanation.

## Related Context

- Opus Clip API requires full upload flow (4 steps) via Google Cloud Storage
- Cannot use `file:///path` — must upload first
- YouTube videos work directly (public URL)
- Credits: 1 credit = 1 minute of video processing