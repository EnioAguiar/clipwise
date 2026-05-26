# Roadmap: ClipWise

**Phases:** 4 | **Requirements:** 34 mapped | **All v1 requirements covered ✓**

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | **Upload + Transcription + Energy** | Video input, local Whisper transcription, audio energy extraction | UPLD-01, UPLD-02, UPLD-03, UPLD-04, TRANS-01, TRANS-02, TRANS-03, TRANS-04, ENERG-01, ENERG-02, ENERG-03, CONF-01, CONF-02, CONF-03, CONF-04, CONF-05 | 16 |
| 2 | **Moment Detection Engine** | Rank moments by energy + transcript, return top N timestamps | ENERG-04, MOMENT-01, MOMENT-02, MOMENT-03, MOMENT-04 | 5 |
| 3 | **Dashboard + Export** | UI to view, filter, select moments and export timestamps | DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, EXPT-01, EXPT-02 | 8 |
| 4 | **Opus Clip Integration** | Automated clip generation via Opus API | OPUS-01, OPUS-02, OPUS-03, OPUS-04, OPUS-05 | 5 |

---

## Phase 1: Upload + Transcription + Energy

**Goal:** Accept video input, transcribe audio locally with Faster Whisper, and extract audio energy using FFmpeg (podcli-style Z-score normalization).

**Requirements:** UPLD-01, UPLD-02, UPLD-03, UPLD-04, TRANS-01, TRANS-02, TRANS-03, TRANS-04, ENERG-01, ENERG-02, ENERG-03, CONF-01, CONF-02, CONF-03, CONF-04, CONF-05

**Success Criteria:**
1. User can upload MP4/MKV/WAV file and see duration info displayed
2. User can paste YouTube link as alternative input
3. Video is saved to /tmp/clipwise with unique ID
4. Faster Whisper produces timestamped transcript JSON (local, free)
5. 60-minute file transcribes without memory issues
6. FFmpeg astats extracts RMS energy per second
7. Z-score normalization computes energy peaks (top 10% loudest)
8. User configures min/max duration (default 30s-60s)
9. User sets target clip count (default 10, range 3-20)
10. User selects output format (9:16 vertical or 1:1 square)
11. User selects mode: auto or manual
12. 60-minute file processes energy analysis without issues
13. Transcript + energy data saved as combined JSON
14. All processing stays local (no cloud, no API costs for transcription/energy)
15. Energy peaks correlate with transcript timestamps for moment detection
16. Configuration persists for session

**Plans:**
- [x] `01-01-PLAN.md` — Backend upload endpoint + YouTube download fallback (complete)
- [x] `01-02-PLAN.md` — Faster Whisper integration + transcript JSON output (complete)
- [ ] `01-03-PLAN.md` — FFmpeg audio energy extraction (astats filter + Z-score)
- [ ] `01-04-PLAN.md` — Configuration UI + settings persistence

---

## Phase 2: Moment Detection Engine

**Goal:** Combine audio energy + transcript to rank and return the best timestamps.

**Requirements:** ENERG-04, MOMENT-01, MOMENT-02, MOMENT-03, MOMENT-04

**Success Criteria:**
1. Energy scores combined with transcript timestamps
2. Moments ranked by combined score (energy + transcript quality)
3. Respect min/max duration from config (default 30s-60s)
4. Return top N moments sorted by score (user-configured, default 10)
5. Output includes timestamp, duration, energy score, transcript snippet

**Note on LLM:** LLM analysis deferred to v2. Phase 1-2 use only audio energy + transcript for moment detection. This keeps costs zero for analysis and lets us validate the approach before adding AI.

**Plans:**
- [ ] `02-01-PLAN.md` — Grok-powered moment detection engine with energy + transcript scoring
- `plan-2.2`: Moment ranking and filtering by duration

---

## Phase 3: Dashboard + Export

**Goal:** Display ranked moments in UI with video player at timestamp, allow filtering/selection, export timestamps manually.

**Requirements:** DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, EXPT-01, EXPT-02

**Success Criteria:**
1. Dashboard shows moments sorted by score descending
2. Video player links directly to moment timestamp
3. Each moment shows energy score and transcript snippet preview
4. User can select/deselect individual moments
5. Slider controls how many top moments to include
6. "Copy timestamps" button copies Opus-compatible format
7. Manual export produces formatted list
8. Waveform + energy peaks visualization

**Plans:**
- [x] `03-01-PLAN.md` — Backend API endpoints + frontend wiring (Wave 1)
- [x] `03-02-PLAN.md` — Dashboard UI: MomentCard, video player, slider (Wave 2)
- [x] `03-03-PLAN.md` — Opus Clip integration + waveform visualization (Wave 3)

---

## Phase 4: Opus Clip Integration

**Goal:** Send selected moments to Opus Clip API and download generated clips automatically.

**Requirements:** OPUS-01, OPUS-02, OPUS-03, OPUS-04, OPUS-05

**Success Criteria:**
1. System authenticates with Opus Clip API
2. Selected moments sent as clip generation requests
3. System polls for completion status
4. Completed clips downloaded to local storage
5. Clip metadata saved alongside files

**Credit Strategy:**
- 1 Opus credit = 1 minute of video
- Clip duration can be shorter than 1 min but costs minimum 1 credit
- Pre-filtering moments = spend credits only on best timestamps
- Example: 60-min live, find 10 best moments (30-60s each) = ~10 credits vs 60 credits if processed whole

**Plans:**
- [x] `04-01-PLAN.md` — Opus Clip API client + video upload workflow (Wave 1)
- [ ] `04-02-PLAN.md` — Timestamp verification + sending + clip polling (Wave 2)

---

## Future (Out of Scope for v1)

- `phase-5`: LLM analysis for semantic engagement (jokes, insights, controversies)
- `phase-6`: 16:9 format support (3-10 min clips)
- `phase-7`: YouTube/Twitch chat replay analysis
- `phase-8`: Speaker diarization (pyannote)
- `phase-9`: Persistent storage + history

---

*Roadmap created: 2025-05-22*
*Last updated: 2025-05-22 after adding audio energy analysis (podcli-style)*