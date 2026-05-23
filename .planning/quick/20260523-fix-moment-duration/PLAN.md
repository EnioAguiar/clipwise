---
status: in-progress
created: 2026-05-23
---

# Fix Moment Duration Validation

## Problem

Gemini returns moments with `segments` array (non-contiguous keep ranges) but:
1. `duration` field = sum of segments (52s in example)
2. `start`/`end` fields = full span (141s in example)

When sending to Opus, frontend uses `start`/`end` → sends 141s clip instead of 52s!

User config: max_clip_duration=90s, but spans of 141s are being sent.

## Root Cause

In `grok_client.py` (and now `gemini_client.py`):
- `duration` is calculated as sum of segment lengths (correct)
- But `end - start` is the full span, not respecting max clip duration

The `_filter_and_sort_moments` function filters by duration, but uses segment sum, not span.

## Fix Required

Backend should validate that `end - start <= max_clip_duration`. If span exceeds max, either:
1. Reject the moment (remove from results)
2. Clamp the end to start + max_clip_duration

Podcli does rejection (line 1043: `if kept_duration > MAX_CLIP_DURATION: continue`).

## Implementation

1. In `moment_ranker.py`: After getting results from Gemini, filter out moments where `end - start > max_clip_duration`
2. Log rejected moments so we know when this happens
3. Verify frontend sends correct timestamps (start, end) to Opus

## Files to modify

- `backend/services/moment_ranker.py`
- `backend/services/gemini_client.py` (update prompt to be stricter)