# Phase 2 Discussion Log

**Date:** 2025-05-23

## Areas Discussed

### 1. LLM Integration Decision
**Question:** Use LLM for moment selection or energy-only?

**Clarification:** User confirmed they have Grok API key. System will use Grok to analyze transcript + energy and choose best moments (like podcli does with Claude).

**Decision:** Use Grok for moment selection (Phase 2)

---

### 2. How Podcli Works
**Question:** Does podcli use LLM for transcription or moment selection?

**Clarification:** Explained:
- Transcription = Faster Whisper (local, no LLM)
- Moment selection = Claude/Codex (LLM analyzes transcript + energy)

Podcli is good at choosing moments because it uses LLM for that step.

**Decision:** ClipWise will use Grok similarly for moment selection

---

### 3. Opus Clip API Role
**Clarification:** Opus Clip API receives timestamps from ClipWise, does NOT choose moments. It's a clip renderer, not a clip selector.

**Decision:** Phase 2 Grok analysis feeds into Phase 3 dashboard, then Phase 4 sends to Opus

---

### 4. Research: Best Practices
**Question:** What do other tools (Opus, podcli) use for moment selection?

**Findings:**
- Podcli: Claude with detailed prompt (hook, standalone, quotability, relevance scoring)
- Opus Clip: Receives timestamps, just renders
- Vizard, Choppity: AI analysis of dialogue, visual cues, emotional cues

**Decision:** Follow podcli approach with Grok

---

### 5. Output Format
**Question:** What should Phase 2 return?

**Decision:** JSON with moments array, each containing:
- start, end, duration
- total_score, scores (hook, standalone, relevance, quotability)
- transcript_snippet
- segments (for tight cuts)
- content_type

---

### 6. Simplification vs Podcli
**Question:** How much to follow podcli?

**Recommendation:** Podcli simplificado (no knowledge base files)

**Decision:** Follow podcli scoring dimensions and cutting rules, but simplified without .podcli/knowledge/ files

---

### 7. Transcript Quality Measurement
**Question:** How to measure transcript quality without LLM?

**Clarification:** Not needed — Grok handles content quality assessment directly

**Decision:** Grok evaluates content quality as part of scoring

---

## Summary

Phase 2 context captured with 7 decisions:
- Use Grok (with API key) for moment selection
- Follow podcli-style scoring (hook, standalone, relevance, quotability)
- Duration and cutting rules from podcli
- JSON output with moments array
- Grok handles content quality assessment
- Overlapping moments handled by Grok prompt instruction
- Output fields: timestamps, scores, snippet, segments, content_type