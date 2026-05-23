# Requirements: ClipWise

**Defined:** 2025-05-22
**Core Value:** Automatically find the best moments in a 1-hour live stream and generate publishable short clips with minimal credit waste.

## v1 Requirements

### Upload

- [ ] **UPLD-01**: User can upload video file (MP4, MKV, WAV)
- [ ] **UPLD-02**: User can paste YouTube link as input source
- [ ] **UPLD-03**: System displays video duration and basic info after upload
- [ ] **UPLD-04**: Video is saved to local temp storage (/tmp/clipwise)

### Transcription

- [ ] **TRANS-01**: System transcribes audio using Faster Whisper (local, no API cost)
- [ ] **TRANS-02**: Transcript includes word-level timestamps
- [ ] **TRANS-03**: Transcript saved as JSON with blocks and timestamps
- [ ] **TRANS-04**: Transcription handles 60+ minute files

### Audio Energy Analysis

- [ ] **ENERG-01**: System extracts RMS energy per second using FFmpeg astats filter
- [ ] **ENERG-02**: System computes Z-score normalization (mean + std deviation)
- [ ] **ENERG-03**: System identifies peak moments (top 10% loudest)
- [ ] **ENERG-04**: Energy scores combined with transcript timestamps

### Moment Detection

- [ ] **MOMENT-01**: System ranks moments by combined energy + transcript score
- [ ] **MOMENT-02**: System respects configured min/max duration (default 30s-60s)
- [ ] **MOMENT-03**: System returns top N moments sorted by score (target 10, range 3-20)
- [ ] **MOMENT-04**: Output includes timestamp, duration, energy score, transcript snippet

### Configuration

- [ ] **CONF-01**: User sets min clip duration (20s to 3min, default 30s)
- [ ] **CONF-02**: User sets max clip duration (30s to 5min, default 60s)
- [ ] **CONF-03**: User sets target number of clips (3-20, default 10)
- [ ] **CONF-04**: User selects output format (vertical 9:16 or square 1:1)
- [ ] **CONF-05**: User selects mode: auto (top moments) or manual (user reviews timestamps)

### Dashboard

- [x] **DASH-01**: Dashboard displays ranked moments list (sorted by energy+transcript score)
- [x] **DASH-02**: Video player with link to moment timestamp
- [x] **DASH-03**: Each moment shows transcript snippet preview and energy score
- [x] **DASH-04**: User can select/deselect which moments to generate
- [x] **DASH-05**: Slider adjusts how many top moments to include
- [x] **DASH-06**: Preview panel shows waveform + energy peaks visualization

### Export

- [ ] **EXPT-01**: User can copy timestamps in Opus-compatible format
- [ ] **EXPT-02**: Manual export generates formatted list ready to paste

### Opus Integration

- [ ] **OPUS-01**: System sends selected moments to Opus Clip API
- [ ] **OPUS-02**: API generates clips at specified timestamps
- [ ] **OPUS-03**: System polls for clip generation status
- [ ] **OPUS-04**: System downloads completed clips locally
- [ ] **OPUS-05**: Clip metadata saved alongside clips

## v2 Requirements (Deferred)

### LLM Analysis (Optional)

- **LLM-01**: LLM analyzes transcript for semantic engagement (jokes, insights, controversies)
- **LLM-02**: LLM provides reasoning for why each moment was selected
- **LLM-03**: Moment types categorized (educacional, engajamento, humor)

### Enhanced Features

- **ENHA-01**: Support 16:9 format for longer clips (3-10 min)
- **ENHA-02**: Chat replay integration to pre-filter moments (YouTube chat)
- **ENHA-03**: Speaker diarization (pyannote) for multi-speaker streams
- **ENHA-04**: Persist transcript JSON for later re-analysis
- **ENHA-05**: History of processed live streams

## Out of Scope

| Feature | Reason |
|---------|--------|
| Cloud hosting | Local venv only per user request |
| Multi-user support | Single-user local tool |
| Direct video editing | Timestamps only; actual editing via Opus API |
| Watermark removal | Not relevant to workflow |
| Mobile app | Desktop-first, local processing |
| Pyannote/speaker diarization | Not needed for timestamp detection |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| UPLD-01 | Phase 1 | Pending |
| UPLD-02 | Phase 1 | Pending |
| UPLD-03 | Phase 1 | Pending |
| UPLD-04 | Phase 1 | Pending |
| TRANS-01 | Phase 1 | Pending |
| TRANS-02 | Phase 1 | Pending |
| TRANS-03 | Phase 1 | Pending |
| TRANS-04 | Phase 1 | Pending |
| ENERG-01 | Phase 1 | Pending |
| ENERG-02 | Phase 1 | Pending |
| ENERG-03 | Phase 1 | Pending |
| ENERG-04 | Phase 2 | Pending |
| MOMENT-01 | Phase 2 | Pending |
| MOMENT-02 | Phase 2 | Pending |
| MOMENT-03 | Phase 2 | Pending |
| MOMENT-04 | Phase 2 | Pending |
| CONF-01 | Phase 1 | Pending |
| CONF-02 | Phase 1 | Pending |
| CONF-03 | Phase 1 | Pending |
| CONF-04 | Phase 1 | Pending |
| CONF-05 | Phase 1 | Pending |
| DASH-01 | Phase 3 | Complete |
| DASH-02 | Phase 3 | Complete |
| DASH-03 | Phase 3 | Complete |
| DASH-04 | Phase 3 | Complete |
| DASH-05 | Phase 3 | Complete |
| DASH-06 | Phase 3 | Complete |
| EXPT-01 | Phase 3 | Pending |
| EXPT-02 | Phase 3 | Pending |
| OPUS-01 | Phase 4 | Pending |
| OPUS-02 | Phase 4 | Pending |
| OPUS-03 | Phase 4 | Pending |
| OPUS-04 | Phase 4 | Pending |
| OPUS-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 34 total
- Mapped to phases: 34
- Unmapped: 0 ✓

---
*Requirements defined: 2025-05-22*
*Last updated: 2025-05-22 after adding audio energy analysis*