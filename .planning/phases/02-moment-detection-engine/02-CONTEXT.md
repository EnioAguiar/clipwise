# Phase 2: Moment Detection Engine - Context

**Gathered:** 2025-05-23
**Status:** Ready for planning

## Phase Boundary

Combine audio energy + transcript to rank and return the best timestamps using Grok AI analysis.

## Canonical References

### Project docs
- `.planning/REQUIREMENTS.md` — Phase 2 requirements (ENERG-04, MOMENT-01 to MOMENT-04)
- `.planning/ROADMAP.md` — Phase 2 goal and success criteria
- `.planning/phases/01-upload-transcription-energy/01-CONTEXT.md` — Phase 1 decisions

### Podcli reference
- `podcli/backend/services/claude_suggest.py` — LLM-based clip selection (primary reference for prompt design)
- `podcli/backend/services/audio_analyzer.py` — energy scoring logic
- `podcli/backend/services/transcript_packer.py` — transcript packing for LLM input

### Tech stack
- `frontend/` — Next.js 14 app (app router, Tailwind, shadcn/ui)
- `backend/main.py` — FastAPI entry point
- `backend/services/transcription.py` — Phase 1 transcription output
- `backend/services/energy.py` — Phase 1 energy output

## Implementation Decisions

### D-01: LLM Provider
- **Grok** (xAI API) — user has API key
- Model: default Grok model (grok-2 or current)

### D-02: Analysis Input
- Grok receives:
  - Transcript text (from Phase 1 `transcript.json` packed via `pack_transcript` logic)
  - Energy data (peak_times, energy scores from Phase 1)
- Config settings (min/max duration, target clips from Phase 1)

### D-03: Moment Selection Prompt
Follow podcli-style prompt with simplified criteria:

**Scoring dimensions (1-5 each):**
- `hook`: Grabs attention in first 3 seconds?
- `standalone`: Makes sense without episode context?
- `relevance`: Matters to target audience?
- `quotability`: Memorable, shareable phrasing?

**Duration rules:**
- Target: {TARGET_CLIP_DURATION_MIN}-{TARGET_CLIP_DURATION_MAX} seconds
- Maximum: {MAX_CLIP_DURATION} seconds (hard limit)
- Minimum: {MIN_CLIP_DURATION} seconds

**Cutting rules:**
- Start at exact moment hook hits — no preamble
- End on complete thought — sentence boundary, mic-drop moment
- If filler in middle, use segments to cut it out
- SHORTER IS BETTER

**Selection criteria:**
- Would YOU stop scrolling for this? If no, skip
- Prioritize: controversial takes, surprising numbers, emotional peaks
- Skip: generic advice, context-dependent references
- Diversify picks across entire timeline (don't cluster in one section)

### D-04: Output Format
```json
{
  "moments": [
    {
      "start": 123.4,
      "end": 168.4,
      "duration": 45,
      "total_score": 16,
      "scores": {
        "hook": 5,
        "standalone": 4,
        "relevance": 4,
        "quotability": 3
      },
      "transcript_snippet": "The key quote from this moment",
      "segments": [
        {"start": 123.4, "end": 140.0},
        {"start": 145.2, "end": 168.4}
      ],
      "content_type": "guest_story|technical_insight|hot_take"
    }
  ]
}
```

**content_type options:** guest_story, technical_insight, hot_take, market_landscape, business_strategy

### D-05: Grok Integration
- API call to Grok with structured prompt
- Returns parsed JSON with moment list
- Falls back to energy-only ranking if API fails

### D-06: Transcript Quality (without LLM)
- Not needed — Grok handles content quality assessment
- Only basic metrics: word density, silence detection

### D-07: Overlapping Moments
- Grok instructed to avoid overlapping moments
- If overlap occurs, higher-scored moment wins
- segments array allows cutting filler while keeping bounds

### D-08: Output Fields
Per moment:
- `start`, `end` (seconds)
- `duration` (seconds, sum of segments)
- `total_score` (sum of 4 dimensions, max 20)
- `scores` (individual 1-5 scores)
- `transcript_snippet` (key quote)
- `segments` (keep-ranges for tight cuts)
- `content_type` (classification)

## Existing Code Insights

### Integration Points
- `backend/services/transcription.py` — loads transcript.json
- `backend/services/energy.py` — loads energy.json, uses peak_times
- `backend/main.py` — add /rank endpoint

### Reusable from Phase 1
- Storage path: `/tmp/clipwise/<video_id>/`
- transcript.json structure
- energy.json structure

## Specific Ideas

- Follow podcli's `_build_prompt` structure but simplified (no knowledge base)
- Use same JSON output structure as podcli for Phase 3 dashboard compatibility
- Config values flow from Phase 1 (min/max duration, target clips)

## Deferred Ideas

None — discussion stayed within phase scope