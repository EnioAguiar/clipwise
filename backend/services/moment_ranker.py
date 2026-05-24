"""
Moment ranking service — combines energy + transcript to rank and filter moments.

Uses Gemini AI for intelligent selection.
Falls back to energy-only ranking if Gemini is unavailable.
"""

import json
import os
from typing import Optional

from .gemini_client import call_gemini_moment_selection, fallback_energy_ranking
from .energy import get_energy_profile, save_energy_data

VIDEO_DIR = "/tmp/clipwise"


def rank_moments(
    video_id: str,
    config: dict,
    use_llm: bool = True,
) -> dict:
    """
    Main entry point — rank all moments for a video.

    Args:
        video_id: unique video identifier
        config: {min_clip_duration, max_clip_duration, target_clips, format}
        use_llm: if True, use Grok; if False, energy-only fallback

    Returns:
        {"moments": [...]} per D-04 output format
    """
    video_dir = os.path.join(VIDEO_DIR, video_id)

    # Load transcript.json
    transcript_path = os.path.join(video_dir, "transcript.json")
    with open(transcript_path, "r") as f:
        transcript_data = json.load(f)

    # Load energy.json (created by Phase 1 energy endpoint)
    energy_path = os.path.join(video_dir, "energy.json")
    if os.path.exists(energy_path):
        with open(energy_path, "r") as f:
            energy_info = json.load(f)
        energy_data = energy_info.get("energy_data", [])
    else:
        # Extract energy if not yet done
        video_path = _find_video_path(video_dir)
        if video_path:
            profile = get_energy_profile(video_path)
            energy_data = profile.get("energy_data", [])
            save_energy_data(
                video_id,
                profile.get("energy_data", []),
                profile.get("segment_scores", []),
                profile.get("peak_times", []),
            )
        else:
            energy_data = []

    # Use Gemini if enabled and available
    if use_llm:
        try:
            print(f"[RANK] Starting moment ranking with config: {config}")
            result = call_gemini_moment_selection(transcript_data, config)
            raw_count = len(result.get("moments", []))
            print(f"[RANK] Gemini returned {raw_count} raw moments")
            # Post-process: filter by span, sort by score
            filtered_result = _filter_and_sort_moments(result, config)
            final_count = len(filtered_result.get("moments", []))
            print(f"[RANK] After filtering: {final_count} valid moments")
            return filtered_result
        except RuntimeError as e:
            # Gemini failed — log and fall back
            print(f"[RANK] Gemini failed: {e}, using energy-only fallback")
            pass

    # Fallback: energy-only ranking
    print(f"[RANK] Using energy-only fallback")
    return fallback_energy_ranking(energy_data, transcript_data, config)


def _filter_and_sort_moments(result: dict, config: dict) -> dict:
    """
    Post-process Gemini output:
    - Filter moments by SPAN (end - start), not segment sum
    - Remove overlaps (higher score wins)
    - Sort by total_score descending
    - Return top N

    IMPORTANT: We validate SPAN, not the "duration" field (which is segment sum).
    The Opus API receives start/end, so span must respect min/max.
    """
    min_dur = config.get("min_clip_duration", 30)
    max_dur = config.get("max_clip_duration", 60)
    target = config.get("target_clips", 10)

    moments = result.get("moments", [])
    
    # Filter by SPAN (end - start), not segment sum duration
    valid_moments = []
    rejected = 0
    for m in moments:
        span = m.get("end", 0) - m.get("start", 0)
        if min_dur <= span <= max_dur:
            valid_moments.append(m)
        else:
            rejected += 1
            print(f"[RANK] Rejected moment: span={span:.1f}s (must be {min_dur}-{max_dur}s)")
    
    if rejected:
        print(f"[RANK] Rejected {rejected} moments for span outside valid range")

    # Remove overlaps
    filtered = []
    used_ranges = []
    for m in sorted(valid_moments, key=lambda x: x.get("total_score", 0), reverse=True):
        start = m.get("start", 0)
        end = m.get("end", 0)
        overlaps = False
        for used_start, used_end in used_ranges:
            if not (end < used_start or start > used_end):
                overlaps = True
                break
        if not overlaps:
            filtered.append(m)
            used_ranges.append((start, end))

    # Return top N
    return {"moments": filtered[:target]}


def _find_video_path(video_dir: str) -> Optional[str]:
    """Find the video file in a video directory."""
    if not os.path.exists(video_dir):
        return None
    for fname in os.listdir(video_dir):
        if fname not in ("transcript.json", "energy.json", "combined.md"):
            return os.path.join(video_dir, fname)
    return None


def save_moments(video_id: str, moments_data: dict) -> str:
    """
    Save ranked moments to /tmp/clipwise/<video_id>/moments.json.

    Returns path to saved file.
    """
    dest_dir = os.path.join(VIDEO_DIR, video_id)
    os.makedirs(dest_dir, exist_ok=True)

    moments_path = os.path.join(dest_dir, "moments.json")
    with open(moments_path, "w") as f:
        json.dump(moments_data, f, indent=2)

    return moments_path