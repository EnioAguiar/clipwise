"""
Grok AI client for moment detection.

Calls Groq API with transcript + energy data to rank moments.
Falls back to energy-only scoring if API fails.
"""

import json
import os
from typing import Optional

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


def call_grok_moment_selection(
    transcript_data: dict,
    energy_data: list[dict],
    config: dict,
) -> dict:
    """
    Send transcript + energy to Groq for moment selection.

    Args:
        transcript_data: {transcript, segments, words, duration, language}
        energy_data: [{time, rms_db}, ...] from energy.json
        config: {min_duration, max_duration, target_clips, ...}

    Returns:
        {"moments": [...]} per D-04 output format

    Raises:
        RuntimeError: if API call fails and fallback is disabled
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set — cannot call Groq API")

    from groq import Groq

    prompt = _build_moment_prompt(transcript_data, energy_data, config)

    client = Groq(api_key=GROQ_API_KEY)

    try:
        chat_completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert video clip selector. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        content = chat_completion.choices[0].message.content
        if content.strip().startswith("```"):
            lines = content.strip().split("\n")
            content = "\n".join(lines[1:-1])
        return json.loads(content)
    except Exception as e:
        raise RuntimeError(f"Groq API failed: {e}") from e


def _build_moment_prompt(transcript_data: dict, energy_data: list[dict], config: dict) -> str:
    """
    Build the moment selection prompt per D-03.

    Scoring dimensions (1-5 each):
    - hook: Grabs attention in first 3 seconds?
    - standalone: Makes sense without episode context?
    - relevance: Matters to target audience?
    - quotability: Memorable, shareable phrasing?

    Duration rules:
    - Target: {TARGET_CLIP_DURATION_MIN}-{TARGET_CLIP_DURATION_MAX} seconds
    - Maximum: {MAX_CLIP_DURATION} seconds (hard limit)
    - Minimum: {MIN_CLIP_DURATION} seconds
    """
    min_dur = config.get("min_clip_duration", 30)
    max_dur = config.get("max_clip_duration", 60)
    target = config.get("target_clips", 10)

    # Pack transcript into markdown (similar to transcript_packer.py)
    transcript_md = _pack_transcript_for_prompt(transcript_data)

    # Add energy peaks
    energy_md = _pack_energy_for_prompt(energy_data)

    return f"""Analyze this video transcript and energy data to find the best moments for short-form clips.

## Video Duration: {transcript_data.get('duration', 0):.1f} seconds

## Transcript:
{transcript_md}

## Energy Peaks (top 20 loudest moments):
{energy_md}

## Configuration:
- Min clip duration: {min_dur}s
- Max clip duration: {max_dur}s
- Target clips: {target}

## Selection Criteria (score 1-5 each):
- **hook**: Grabs attention in first 3 seconds?
- **standalone**: Makes sense without episode context?
- **relevance**: Matters to target audience?
- **quotability**: Memorable, shareable phrasing?

## Rules:
- Start at exact moment hook hits — no preamble
- End on complete thought — sentence boundary, mic-drop moment
- If filler in middle, use segments array to cut it out
- SHORTER IS BETTER
- Diversify picks across entire timeline (don't cluster in one section)
- Avoid overlapping moments — if overlap occurs, higher-scored moment wins

## Output Format (return ONLY valid JSON):
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
      "content_type": "guest_story|technical_insight|hot_take|market_landscape|business_strategy"
    }}
  ]
}}

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
    # Sort by time and take top 20
    sorted_energy = sorted(energy_data, key=lambda e: e.get("time", 0))
    top_peaks = sorted_energy[:20]
    return "\n".join([f"[{e.get('time', 0):.1f}s] {e.get('rms_db', 0):.1f}dB" for e in top_peaks])


def fallback_energy_ranking(
    energy_data: list[dict],
    transcript_data: dict,
    config: dict,
) -> dict:
    """
    Fallback: rank moments by energy only when Grok API fails.

    Uses energy scores from Phase 1 energy.json combined with
    transcript timestamps to produce ranked moments.
    """
    min_dur = config.get("min_clip_duration", 30)
    max_dur = config.get("max_clip_duration", 60)
    target = config.get("target_clips", 10)

    # Sort energy peaks by rms_db descending
    sorted_peaks = sorted(energy_data, key=lambda e: e.get("rms_db", -999), reverse=True)

    moments = []
    used_ranges = []

    for peak in sorted_peaks:
        if len(moments) >= target:
            break

        peak_time = peak.get("time", 0)
        duration = min_dur  # default duration

        # Check if this overlaps with existing moments
        start = peak_time
        end = peak_time + duration

        overlaps = False
        for used_start, used_end in used_ranges:
            if not (end < used_start or start > used_end):
                overlaps = True
                break

        if not overlaps:
            # Find transcript snippet near this time
            snippet = _find_snippet_at(transcript_data, peak_time)
            moments.append({
                "start": round(peak_time, 1),
                "end": round(end, 1),
                "duration": duration,
                "total_score": int(peak.get("rms_db", 0) + 60),  # normalize from dB
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
    # Nearest segment
    closest = min(
        transcript_data.get("segments", []),
        key=lambda s: min(abs(s.get("start", 0) - time), abs(s.get("end", 0) - time)),
        default=None
    )
    if closest:
        return closest.get("text", "").strip()[:200]
    return ""