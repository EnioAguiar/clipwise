---
status: testing
phase: 04-opus-clip-integration
source: [04-01-SUMMARY.md, 04-02-SUMMARY.md]
started: 2026-05-25T19:05:00Z
updated: 2026-05-25T19:05:00Z
---

## Current Test

number: 1
name: Backend Opus endpoints respond
expected: |
  Backend server starts without errors.
  Endpoints respond:
  - POST /opus/upload-link returns {upload_id, url}
  - POST /opus/upload-complete returns {status: "complete"}
  - POST /opus/store-youtube returns {status: "stored"}
  - POST /opus/send-moments returns {status: "sent", project_id}
  - GET /opus/status/{project_id} returns {status, clips}
awaiting: user response

## Tests

### 1. Backend Opus Endpoints
expected: Backend server starts. All 5 Opus endpoints respond correctly.
result: pending

### 2. OpusUploadButton - Render
expected: Button "Subir vídeo para Opus" appears in the UI. Disabled until moments are ranked.
result: pending

### 3. OpusUploadButton - YouTube Skip
expected: For YouTube videos, clicking "Subir vídeo para Opus" shows success immediately (no upload needed).
result: pending

### 4. OpusUploadButton - Progress
expected: For uploaded videos, clicking button shows progress bar during upload. After upload, shows "Vídeo enviado! Agora você pode enviar os momentos."
result: pending

### 5. TimestampVerificationModal - Open
expected: Clicking "Enviar pro Opus" on a moment opens modal with video preview at that timestamp.
result: pending

### 6. TimestampVerificationModal - Actions
expected: Modal shows moment details (start time, duration, score, transcript). "Confirmar" sends to Opus. "Cancelar" closes modal.
result: pending

### 7. OpusTimestampSender - Enviar todos
expected: "Enviar todos" button sends all moments at once without individual verification. Each moment shows sent status.
result: pending

### 8. OpusTimestampSender - Disabled State
expected: All send buttons are disabled until video upload is complete. After upload, buttons become enabled.
result: pending

### 9. OpusTimestampSender - Status Icons
expected: Each moment shows status icon: idle (gray), sending (blue spinner), sent (green check), error (red alert).
result: pending

### 10. Cold Start Smoke Test
expected: Kill any running servers. Clear /tmp/clipwise/. Start backend and frontend from scratch. Server boots without errors.
result: pending

## Summary

total: 10
passed: 0
issues: 0
pending: 10
skipped: 0
blocked: 0

## Gaps

[none yet]