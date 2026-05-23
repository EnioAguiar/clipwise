# Codebase Concerns

**Analysis Date:** 2026-05-23

## Tech Debt

**Video processor complexity:**
- Issue: `podcli/backend/services/video_processor.py` is 2990 lines — monolithic function handling multiple responsibilities (cutting, cropping, burning captions, encoding). No clear separation of concerns.
- Files: `podcli/backend/services/video_processor.py`
- Impact: Difficult to test, fragile when modifying. Adding a new caption style or crop strategy requires navigating deeply nested conditionals.
- Fix approach: Extract crop strategies into separate strategy classes, isolate FFmpeg command building into dedicated encoder module.

**Dual backend architecture:**
- Issue: Two separate backends exist — `backend/` (FastAPI, Grok integration) and `podcli/backend/` (Python CLI). They share service logic (transcription, energy) but have duplicated code paths and different entry points.
- Files: `backend/main.py`, `podcli/backend/main.py`
- Impact: Inconsistent behavior, maintenance overhead, unclear which backend to use for which workflow.
- Fix approach: Unify into single backend with clear routing based on task type. Extract shared services to a common package.

**Transcript cache race conditions:**
- Issue: `podcli/src/services/transcript-cache.ts` reads/writes JSON files directly without file locking. Concurrent access from multiple processes could corrupt cache.
- Files: `podcli/src/services/transcript-cache.ts`
- Impact: Cache corruption leads to silent transcription failures or incorrect captions burned into clips.
- Fix approach: Use atomic rename pattern (write to temp file, then rename) or implement proper file locking.

**Hardcoded path dependencies:**
- Issue: `backend/services/storage.py` uses `/tmp/clipwise` directly; `podcli/backend/main.py` uses relative `.env` loading that could fail silently.
- Files: `backend/services/storage.py`, `podcli/backend/main.py:14-18`
- Impact: Fails on systems without `/tmp/` write access or when `.env` is missing.
- Fix approach: Use `paths.config` from `podcli/src/config/paths.ts` consistently. Add validation at startup.

**Energy extraction fallback masking real errors:**
- Issue: `podcli/backend/services/audio_analyzer.py:61` silently falls back to `_fallback_energy` when `astats` returns no data. This could hide FFmpeg installation issues or corrupt audio tracks.
- Files: `podcli/backend/services/audio_analyzer.py:61`
- Impact: Noisy energy data produces bad clip suggestions without any warning to the user.
- Fix approach: Log a warning when falling back, emit a flag in the result dict indicating fallback was used.

## Known Bugs

**No TODOs/FIXMEs found — legacy tech debt tracked informally:**
- Issue: No formal bug tracking in codebase. Issues are fixed ad-hoc when discovered.
- Impact: Same bugs may be reintroduced across sessions.
- Workaround: Maintain a `CONCERNS.md` like this document.

**Error handling in `clip_generator.py` swallows subprocess errors:**
- Issue: `podcli/backend/services/clip_generator.py` catches `ProcError` but returns empty clip on failure with minimal error context.
- Files: `podcli/backend/services/clip_generator.py`
- Trigger: FFmpeg fails due to codec issues, missing audio stream, or corrupted video.
- Workaround: Check logs for stderr output from `proc_run`.

**Lambda closure capture in batch handler:**
- Issue: `podcli/backend/main.py:154-156` uses `_i=i` in lambda to capture loop variable. While this works in Python 3, the pattern is fragile.
- Files: `podcli/backend/main.py:154`
- Trigger: Refactoring could break the capture if the lambda is extracted.
- Workaround: Use `functools.partial` or explicit default argument `_i=i`.

## Security Considerations

**API key exposure in environment:**
- Risk: `backend/.env` contains `GROQ_API_KEY`, `OPUS_API_KEY`. `.gitignore` should prevent commits but the file exists in a non-standard location.
- Files: `backend/.env`, `.gitignore`
- Current mitigation: `.gitignore` excludes `.env`
- Recommendations: Never commit `.env`, use secret management (env vars injected at deploy time), add pre-commit hook to verify.

**Shell injection in `proc_run`:**
- Risk: `podcli/backend/utils/proc.py` constructs shell commands. If any path parameter contains untrusted input, shell injection is possible.
- Files: `podcli/backend/utils/proc.py`
- Current mitigation: Input validation in calling code
- Recommendations: Pass commands as argument arrays to `subprocess.run` with `shell=False`.

**CORS allows localhost:3000 only:**
- Risk: `backend/main.py:19-25` sets `allow_origins=["http://localhost:3000"]`. This is restrictive but correct for local dev. Staging/prod would need different config.
- Files: `backend/main.py`
- Current mitigation: Hardcoded origins
- Recommendations: Make CORS origins configurable via environment, default to locked down.

## Performance Bottlenecks

**Video transcription is single-threaded:**
- Problem: Whisper transcription processes entire video in one pass. For 3-hour podcasts this can take 30+ minutes with no progress indication.
- Files: `podcli/backend/services/transcription.py`
- Cause: Sequential processing, no chunking strategy
- Improvement path: Implement chunked transcription with periodic progress saves, allow resume on interruption.

**FFmpeg processes video twice for caption burn:**
- Problem: `clip_generator.py` cuts then re-crops then burns captions — multiple transcode passes that each re-decode video.
- Files: `podcli/backend/services/clip_generator.py`
- Cause: Chained function calls each run separate FFmpeg commands
- Improvement path: Combine operations into single FFmpeg filter graph where possible.

**Energy analysis decodes entire video:**
- Problem: `audio_analyzer.py:37` uses `-vn` to skip video but still processes entire audio track with no chunking.
- Files: `podcli/backend/services/audio_analyzer.py`
- Cause: FFmpeg astats filter requires full stream
- Improvement path: Use segmented analysis with parallel window processing.

**Remotion rendering is heavyweight:**
- Problem: `remotion/` is bundled separately and requires npm prebundle step. Remotion studio is heavyweight for simple caption burns.
- Files: `podcli/remotion/`
- Cause: Used for animated captions (karaoke, branded) — overkill for static captions
- Improvement path: Consider switching to pure FFmpeg ASS subtitles for simple styles, reserve Remotion for complex animated captions only.

## Fragile Areas

**Caption renderer brittle FFmpeg filter chain:**
- Files: `podcli/backend/services/caption_renderer.py`
- Why fragile: Long VF strings with hardcoded positions, timing expressions that break if input resolution varies.
- Safe modification: Test with multiple resolutions (1080p, 4K, vertical 9:16)
- Test coverage: `test_corrections.py`, `test_encoder.py` exist but don't cover resolution edge cases

**Face detection timeout cascades:**
- Files: `podcli/backend/services/face_detector.py`, `podcli/backend/services/face_analysis.py`
- Why fragile: Face detection has no timeout protection in main flow. If model loading hangs, entire clip creation blocks indefinitely.
- Safe modification: Add explicit timeouts to all ML model calls
- Test coverage: `test_face_track_helpers.py` tests logic but not timeout behavior

**Path resolution inconsistencies:**
- Files: `podcli/src/services/asset-manager.ts:63`, `podcli/src/services/asset-manager.ts:70`
- Why fragile: Returns `null` on path resolution failure — caller must check and handle explicitly.
- Safe modification: Throw typed errors instead, let caller decide recovery
- Test coverage: `test_asset_store.py` only

## Scaling Limits

**Local filesystem storage:**
- Current capacity: `/tmp/clipwise` and `.podcli/` directories — limited by disk space
- Limit: No cleanup policy, files accumulate until disk full
- Scaling path: Implement TTL-based cleanup, move to object storage (S3-compatible)

**In-memory transcript cache:**
- Current capacity: Single `TranscriptCache` instance per server
- Limit: Large videos (3+ hour podcasts) produce ~50MB transcript JSON — memory pressure
- Scaling path: Stream transcript parsing, lazy-load segments

**No job queue — synchronous processing:**
- Current capacity: One clip renders at a time per process
- Limit: Batch operations block, no parallelism without multiple instances
- Scaling path: Add job queue (Redis/RabbitMQ) with worker pool

## Dependencies at Risk

**Remotion 4.0.441:**
- Risk: Major version. Breaking changes in 4.x have caused build failures in past upgrades.
- Impact: `npm run remotion:prebundle` fails, all caption rendering breaks
- Migration plan: Lock to exact version in `package.json`, test upgrades in staging first

**Whisper API compatibility:**
- Risk: `services.transcription.py` uses `whisper` package. API changes between versions may break transcription.
- Impact: Transcription silently produces different quality results without error
- Migration plan: Pin whisper version, add quality regression tests with known transcripts

**FFmpeg binary dependency:**
- Risk: All video processing requires `ffmpeg` binary in PATH. No fallback if missing.
- Impact: Entire pipeline fails with unhelpful error message
- Migration plan: Bundle ffmpeg or verify presence at startup with clear error message

## Missing Critical Features

**No video format validation:**
- Problem: Accepts any file FFmpeg can open. No validation for codec support, resolution limits, duration limits.
- Blocks: Users discover issues late in rendering pipeline
- Priority: High

**No authentication/authorization:**
- Problem: `backend/main.py` has no auth. `podcli/src/server.ts` MCP tools have no access control.
- Blocks: Multi-user deployments, API key management
- Priority: High for production deployment

**No incremental clip export:**
- Problem: Batch operations either export all or none. Can't resume a failed batch.
- Blocks: Long batch jobs lose progress on failure
- Priority: Medium

**No transcript edit capability:**
- Problem: Corrections are global key-value pairs. Can't edit specific segments.
- Blocks: Users can't fix Whisper errors in context
- Priority: Medium

## Test Coverage Gaps

**Untested error paths:**
- What's not tested: Network failures in `grok_client.py`, malformed JSON responses, FFmpeg missing
- Files: `backend/services/grok_client.py`, `podcli/backend/utils/proc.py`
- Risk: Silent failures and incorrect fallback behavior
- Priority: Medium

**No integration tests for full pipeline:**
- What's not tested: End-to-end video → clip flow with real FFmpeg
- Files: `podcli/tests/` (unit tests only)
- Risk: Bugs in service orchestration not caught until manual testing
- Priority: High

**Caption rendering resolution edge cases:**
- What's not tested: 4K input, unusual aspect ratios, variable frame rates
- Files: `podcli/backend/services/caption_renderer.py`
- Risk: Broken output on non-standard videos
- Priority: Medium

**Face tracking in low-quality video:**
- What's not tested: Blurry faces, multiple faces, no faces scenarios
- Files: `podcli/backend/services/face_track_helpers.py`
- Risk: Incorrect crop target selection
- Priority: Low

---

*Concerns audit: 2026-05-23*