"""
Gemini AI client for moment detection.

Calls Gemini API with transcript + energy data to rank moments.
Falls back to energy-only scoring if API fails.
"""

import json
import math
import os
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def call_gemini_moment_selection(
    transcript_data: dict,
    config: dict,
) -> dict:
    """
    Send transcript to Gemini for moment selection.
    
    For long transcripts (>45 min or >180 segments), uses bucketing strategy
    to avoid timeout and token limits.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set — cannot call Gemini API")
    
    print(f"[GEMINI] Sending request with config: min={config.get('min_clip_duration', 30)}, max={config.get('max_clip_duration', 60)}, target={config.get('target_clips', 10)}")

    # Check if we should use bucketing
    duration = transcript_data.get("duration", 0)
    segments = transcript_data.get("segments", [])
    use_bucketing = duration >= 45 * 60 or len(segments) >= 180
    
    if use_bucketing:
        print(f"[GEMINI] Long transcript detected (duration={duration:.0f}s, segments={len(segments)}). Using bucketing strategy.")
        return _call_gemini_with_buckets(transcript_data, config)
    
    # Single call for shorter transcripts
    return _call_gemini_single(transcript_data, config)


def _call_gemini_single(transcript_data: dict, config: dict) -> dict:
    """Single Gemini API call for regular transcripts."""
    prompt = _build_moment_prompt(transcript_data, config)
    
    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    print(f"[GEMINI] Sending request to {GEMINI_MODEL}...")
    
    try:
        response = requests.post(GEMINI_URL, headers=headers, json=body, timeout=180)
        response.raise_for_status()
        result = response.json()
        
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        print(f"[GEMINI] Raw response length: {len(text)} chars")
        print(f"[GEMINI] Raw response (first 500 chars): {text[:500]}")
        
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
            print(f"[GEMINI] Stripped markdown wrapper, JSON length: {len(text)}")
        
        parsed = json.loads(text)
        moments = parsed.get("moments", [])
        moments_count = len(moments)
        print(f"[GEMINI] Parsed {moments_count} moments")
        
        for i, m in enumerate(moments[:3]):
            scores = m.get("scores", {})
            total = m.get("total_score", 0)
            span = m.get("end", 0) - m.get("start", 0)
            print(f"[GEMINI] Moment {i+1}: scores={scores}, total_score={total}, span={span:.1f}s")
        
        return parsed
        
    except requests.exceptions.Timeout:
        raise RuntimeError("Gemini API timeout after 180s")
    except Exception as e:
        print(f"[GEMINI] Error: {e}")
        raise RuntimeError(f"Gemini API failed: {e}") from e


def _call_gemini_with_buckets(transcript_data: dict, config: dict) -> dict:
    """
    Process long transcripts by dividing into buckets (like podcli).
    
    Each bucket is processed separately to avoid timeout.
    Results are aggregated and deduplicated.
    """
    min_dur = config.get("min_clip_duration", 30)
    max_dur = config.get("max_clip_duration", 60)
    target = config.get("target_clips", 10)
    
    duration = transcript_data.get("duration", 0)
    segments = transcript_data.get("segments", [])
    
    # Create buckets (3-6 based on duration) - like podcli: ~25 min per bucket
    bucket_count = min(6, max(3, math.ceil(duration / 1500)))  # 25 min per bucket
    bucket_size = duration / bucket_count
    
    print(f"[GEMINI] Creating {bucket_count} buckets (~{bucket_size/60:.0f} min each)")
    
    all_moments = []
    
    for idx in range(bucket_count):
        bucket_start = idx * bucket_size
        bucket_end = duration if idx == bucket_count - 1 else (idx + 1) * bucket_size
        
        # Get segments in this bucket
        bucket_segments = [s for s in segments if s.get("start", 0) >= bucket_start and s.get("start", 0) < bucket_end]
        
        if len(bucket_segments) < 3:
            print(f"[GEMINI] Bucket {idx+1}: too few segments, skipping")
            continue
        
        # Create transcript data for this bucket
        bucket_transcript = {
            "duration": bucket_end - bucket_start,
            "segments": bucket_segments,
            "transcript": " ".join(s.get("text", "") for s in bucket_segments)
        }
        
        print(f"[GEMINI] Bucket {idx+1}/{bucket_count}: {int(bucket_start//60)}:{int(bucket_start%60):02d}-{int(bucket_end//60)}:{int(bucket_end%60):02d} ({len(bucket_segments)} segments)")
        
        # Build prompt for bucket (smaller target per bucket)
        bucket_target = max(2, target // bucket_count + 1)
        bucket_config = config.copy()
        bucket_config["target_clips"] = bucket_target
        
        prompt = _build_moment_prompt(bucket_transcript, bucket_config)
        
        headers = {
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json"
        }
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(GEMINI_URL, headers=headers, json=body, timeout=180)
            response.raise_for_status()
            result = response.json()
            
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            
            parsed = json.loads(text)
            bucket_moments = parsed.get("moments", [])
            print(f"[GEMINI] Bucket {idx+1} returned {len(bucket_moments)} moments")
            all_moments.extend(bucket_moments)
            
        except Exception as e:
            print(f"[GEMINI] Bucket {idx+1} failed: {e}")
            continue
    
    print(f"[GEMINI] Total moments from all buckets: {len(all_moments)}")
    return {"moments": all_moments}


def _build_moment_prompt(transcript_data: dict, config: dict) -> str:
    """
    Build the moment selection prompt (like podcli).
    """
    min_dur = config.get("min_clip_duration", 30)
    max_dur = config.get("max_clip_duration", 60)
    target = config.get("target_clips", 10)

    transcript_md = _pack_transcript_for_prompt(transcript_data)
    segment_count = len(transcript_data.get("segments", []))
    duration_min = transcript_data.get("duration", 0) / 60

    return f"""You are a viral clip editor for TikTok and YouTube Shorts. Find the {target} most scroll-stopping moments in this video transcript.

IMPORTANT: Return ONLY valid JSON. No markdown, no explanation, no code fences.

TIMESTAMP FORMAT: All timestamps in the transcript are in SECONDS (e.g., [123.4s]).
All timestamps you return MUST be in SECONDS as numbers (e.g., 123.4), NOT minutes:seconds.

DURATION RULES (CRITICAL):
- Target: {min_dur}-{max_dur} seconds (this is the viral sweet spot)
- Maximum: {max_dur} seconds (absolute hard limit — anything longer WILL FAIL)
- Minimum: {min_dur} seconds (too short = no payoff)
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
      "title": "First strong sentence from the moment",
      "start": 123.4,
      "end": 168.4,
      "duration": 40,
      "content_type": "guest_story",
      "scores": {{"hook": 4, "standalone": 5, "relevance": 4, "quotability": 3}},
      "total_score": 16,
      "transcript_snippet": "The key quote from this moment",
      "segments": [{{"start": 123.4, "end": 140.0}}, {{"start": 145.2, "end": 168.4}}]
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
- Solution: adjust start/end to be close to segment sum, or use single segment

Rules:
- Final clip duration (sum of segments) MUST be {min_dur}-{max_dur} seconds
- Each segment must start and end on COMPLETE SENTENCES — never mid-thought
- The LAST segment must end on a sentence that feels like a natural conclusion
- Must make sense standalone when stitched together
- Sort clips by timestamp order

Transcript ({segment_count} segments, ~{duration_min:.0f} min):

{transcript_md}

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