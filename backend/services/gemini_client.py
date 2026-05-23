"""
Gemini AI client for moment detection.

Calls Gemini API with transcript + energy data to rank moments.
Falls back to energy-only scoring if API fails.
"""

import json
import os
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def call_gemini_moment_selection(
    transcript_data: dict,
    energy_data: list[dict],
    config: dict,
) -> dict:
    """
    Send transcript + energy to Gemini for moment selection.

    Args:
        transcript_data: {transcript, segments, words, duration, language}
        energy_data: [{time, rms_db}, ...] from energy.json
        config: {min_clip_duration, max_clip_duration, target_clips, ...}

    Returns:
        {"moments": [...]} per output format

    Raises:
        RuntimeError: if API call fails and fallback is disabled
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set — cannot call Gemini API")

    prompt = _build_moment_prompt(transcript_data, energy_data, config)

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    print(f"[GEMINI] Sending request to {GEMINI_MODEL}...")
    
    try:
        response = requests.post(GEMINI_URL, headers=headers, json=body, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        # Extract text from Gemini response
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        print(f"[GEMINI] Raw response length: {len(text)} chars")
        
        # Parse JSON from text (Gemini might wrap in ```json)
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        
        parsed = json.loads(text)
        moments_count = len(parsed.get("moments", []))
        print(f"[GEMINI] Parsed moments count: {moments_count}")
        return parsed
        
    except requests.exceptions.Timeout:
        raise RuntimeError("Gemini API timeout after 120s")
    except Exception as e:
        raise RuntimeError(f"Gemini API failed: {e}") from e


def _build_moment_prompt(transcript_data: dict, energy_data: list[dict], config: dict) -> str:
    """
    Build the moment selection prompt (same as Groq version).

    Duration rules (CRITICAL):
    - Target: {min}-{max} seconds (this is the viral sweet spot)
    - Maximum: {max} seconds (absolute hard limit — clips longer will be rejected)
    - Minimum: {min} seconds (too short = no payoff, will be rejected)
    - SHORTER IS BETTER. A punchy 25s clip outperforms a 40s clip every time.
    """
    min_dur = config.get("min_clip_duration", 30)
    max_dur = config.get("max_clip_duration", 60)
    target = config.get("target_clips", 10)
    target_dur = min_dur

    transcript_md = _pack_transcript_for_prompt(transcript_data)
    energy_md = _pack_energy_for_prompt(energy_data)

    return f"""You are a viral clip editor for TikTok and YouTube Shorts. Find the {target * 5} most scroll-stopping moments in this video transcript.

IMPORTANT: Return ONLY valid JSON. No markdown, no explanation, no code fences.

IMPORTANT: Generate MORE candidates than you need — {target * 5} moments. The filter will validate span duration.

TIMESTAMP FORMAT: All timestamps in the transcript are in SECONDS (e.g., [123.4s]).
All timestamps you return MUST be in SECONDS as numbers (e.g., 123.4), NOT minutes:seconds.

DURATION RULES (CRITICAL):
- Target: {target_dur}-{max_dur} seconds (this is the viral sweet spot)
- Maximum: {max_dur} seconds (absolute hard limit — clips longer will be REJECTED)
- Minimum: {min_dur} seconds (too short = no payoff, will be REJECTED)
- SHORTER IS BETTER. A punchy 25s clip outperforms a 40s clip every time.
- If a thought takes longer than {max_dur}s, use segments to cut the filler in the middle

CUTTING RULES (CRITICAL):
- Cut TIGHT. Every second must earn its place.
- Start at the exact moment the hook hits — no preamble, no "so", no "well"
- End the MOMENT the point lands with a complete thought — don't trail off
- NEVER cut mid-sentence or mid-thought. The viewer must feel closure.
- The last sentence must feel like a natural ending, a punchline, or a mic-drop
- If there's filler/tangent in the middle, use multiple segments to skip it
- A 30s clip with zero dead weight beats a {max_dur}s clip with fluff

MOMENT SELECTION (think like a TikTok editor):
- Would YOU stop scrolling for this? If no, skip it.
- First 3 seconds must HOOK — a bold claim, shocking number, or provocative question
- Must make complete sense standalone — no "as I mentioned" or "going back to"
- Must end on a COMPLETE THOUGHT — sentence boundary, natural pause, or mic-drop moment
- Single focused idea — one concept, fully delivered, no loose threads
- Prioritize: controversial takes, surprising numbers, founder war stories, "wait what?" moments, emotional peaks
- Skip: generic advice, obvious statements, context-dependent references
- Search the ENTIRE timeline and diversify the picks. Do not cluster all clips in one section.

Score each moment on 4 dimensions (1-5 each):
- hook: Grabs attention in first 3 seconds?
- standalone: Makes sense without episode context?
- relevance: Matters to target audience?
- quotability: Memorable, shareable phrasing?

Classify each as: guest_story | technical_insight | hot_take | market_landscape | business_strategy

Return this exact JSON structure:
{{
  "moments": [
    {{
      "start": 123.4,
      "end": 168.4,
      "duration": 45,
      "total_score": 16,
      "scores": {{"hook": 5, "standalone": 4, "relevance": 4, "quotability": 3}},
      "transcript_snippet": "The key quote from this moment",
      "segments": [{{"start": 123.4, "end": 140.0}}, {{"start": 145.2, "end": 168.4}}],
      "content_type": "guest_story"
    }}
  ]
}}

SEGMENTS RULES:
- "segments" is an array of keep-ranges within the clip. Use it to CUT OUT dead weight.
- If the moment is clean with no filler, use a single segment: [{{"start": X, "end": Y}}]
- If there's a ramble/tangent/filler in the middle, split into multiple segments that skip it
- Each segment must start and end on sentence boundaries
- The rendered video will stitch these segments together seamlessly
- "duration" = total kept time (sum of all segment lengths), NOT end - start

IMPORTANT - SPAN VALIDATION:
- The outer bounds (start/end) define what Opus API will receive
- Your returned "end" minus "start" MUST be {min_dur}-{max_dur} seconds
- If you use segments to skip filler, the span will be larger than duration
- Example: if start=100, end=200, but segments are only 80s total → SPAN=100s > max={max_dur}s → REJECTED
- Solution: if you use segments, adjust start/end to be close to segment sum
- OR: use a single segment that covers the full moment without internal gaps

Rules:
- Final clip duration (sum of segments) MUST be {min_dur}-{max_dur} seconds (target {target_dur}-{max_dur}s)
- Each segment must start and end on COMPLETE SENTENCES — never mid-thought
- The LAST segment must end on a sentence that feels like a natural conclusion
- Must make sense standalone when stitched together
- Sort clips by timestamp order

Transcript:
{transcript_md}

Energy Peaks (top 20 loudest moments):
{energy_md}

Return JSON only — no markdown, no explanation."""


def _pack_transcript_for_prompt(transcript_data: dict) -> str:
    """Pack transcript segments into readable text for prompt."""
    lines = []
    for seg in transcript_data.get("segments", []):
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        text = seg.get("text", "").strip()
        if text:
            lines.append(f"[{start:.1f}-{end:.1f}] {text}")
    return "\n".join(lines)


def _pack_energy_for_prompt(energy_data: list[dict]) -> str:
    """Pack energy peaks into readable format for prompt."""
    if not energy_data:
        return "No energy data available"
    sorted_energy = sorted(energy_data, key=lambda e: e.get("rms_db", -999), reverse=True)
    top_peaks = sorted_energy[:20]
    return "\n".join([f"[{e.get('time', 0):.1f}s] {e.get('rms_db', 0):.1f}dB" for e in top_peaks])


def fallback_energy_ranking(
    energy_data: list[dict],
    transcript_data: dict,
    config: dict,
) -> dict:
    """
    Fallback: rank moments by energy only when Gemini API fails.

    Uses energy scores from Phase 1 energy.json combined with
    transcript timestamps to produce ranked moments.
    """
    min_dur = config.get("min_clip_duration", 30)
    max_dur = config.get("max_clip_duration", 60)
    target = config.get("target_clips", 10)

    sorted_peaks = sorted(energy_data, key=lambda e: e.get("rms_db", -999), reverse=True)

    moments = []
    used_ranges = []

    for peak in sorted_peaks:
        if len(moments) >= target:
            break

        peak_time = peak.get("time", 0)
        duration = min_dur

        start = peak_time
        end = peak_time + duration

        overlaps = False
        for used_start, used_end in used_ranges:
            if not (end < used_start or start > used_end):
                overlaps = True
                break

        if not overlaps:
            snippet = _find_snippet_at(transcript_data, peak_time)
            moments.append({
                "start": round(peak_time, 1),
                "end": round(end, 1),
                "duration": duration,
                "total_score": int(peak.get("rms_db", 0) + 60),
                "scores": {
                    "hook": 3,
                    "standalone": 3,
                    "relevance": 3,
                    "quotability": 3,
                },
                "transcript_snippet": snippet,
                "segments": [{"start": round(peak_time, 1), "end": round(end, 1)}],
                "content_type": "technical_insight",
            })
            used_ranges.append((start, end))

    return {"moments": moments}


def _find_snippet_at(transcript_data: dict, time: float, window: float = 30.0) -> str:
    """Find transcript text near a given time."""
    for seg in transcript_data.get("segments", []):
        if seg.get("start", 0) <= time <= seg.get("end", 0):
            return seg.get("text", "").strip()[:200]
    closest = min(
        transcript_data.get("segments", []),
        key=lambda s: min(abs(s.get("start", 0) - time), abs(s.get("end", 0) - time)),
        default=None
    )
    if closest:
        return closest.get("text", "").strip()[:200]
    return ""