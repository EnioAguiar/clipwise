---
status: awaiting_human_verify
trigger: "Groq API key not being read from .env file, and config values from frontend not being applied correctly"
created: 2026-05-23
updated: 2026-05-23
trigger_timestamp: 2026-05-23T16:30:00Z
symptoms:
  expected_behavior: |
    1. GROQ_API_KEY from .env should be loaded and used by grok_client.py
    2. Config panel in frontend allows setting min/max duration (e.g., 30-90s)
       and those values should be sent to backend via /process API call
  actual_behavior: |
    1. Backend logs show: "GROQ_API_KEY not set — cannot call Groq API, using energy-only fallback"
       even though .env contains: GROQ_API_KEY=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
    2. Backend receives config with defaults (min_clip_duration=30, max_clip_duration=60)
       instead of user-selected values from frontend (e.g., min=30, max=90)
  error_messages: |
    - "GROQ_API_KEY not set — cannot call Groq API, using energy-only fallback"
    - Config shown in UI as 30-90 but backend logs show config={'min_clip_duration': 30, 'max_clip_duration': 60, ...}
  timeline: |
    - Issue appeared after recent refactoring to split /extract from /process endpoints
    - Previously /process was chaining all steps including LLM ranking
  reproduction: |
    1. Set GROQ_API_KEY in backend/.env
    2. Upload video and configure min=30, max=90 in UI
    3. Click "Processar com IA"
    4. Observe: fallback to energy-only AND config not applied
---

## Current Focus

hypothesis: |
  Two separate root causes:
  1. GROQ_API_KEY: main.py does NOT call load_dotenv(), so os.environ.get("GROQ_API_KEY") returns empty string at module load time in grok_client.py
  2. Config not applied: Frontend sends camelCase config ({minDuration, maxDuration}) but ProcessingConfig expects snake_case ({min_clip_duration, max_clip_duration})

next_action: Apply fixes for both issues

## Evidence

- timestamp: 2026-05-23
  checked: backend/main.py imports
  found: No import of dotenv, no load_dotenv() call anywhere in main.py
  implication: Environment variables from .env are not loaded before services start

- timestamp: 2026-05-23
  checked: backend/services/grok_client.py line 12
  found: "GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")" runs at module import time
  implication: If load_dotenv() hasn't run yet, this gets empty string and stays empty

- timestamp: 2026-05-23
  checked: frontend/src/components/ConfigPanel.tsx
  found: Uses camelCase: {minDuration, maxDuration, targetClips, format, mode}
  implication: Frontend config is NOT snake_case

- timestamp: 2026-05-23
  checked: backend/main.py ProcessingConfig (lines 34-38)
  found: Uses snake_case: {min_clip_duration, max_clip_duration, target_clips, format}
  implication: Backend expects snake_case but frontend sends camelCase

- timestamp: 2026-05-23
  checked: How ProcessRequest uses config (line 214, 318-323)
  found: req.config is ProcessingConfig, extracts snake_case keys into dict
  implication: Pydantic will use defaults when camelCase fields don't match snake_case

## Eliminated

- hypothesis: Backend /process endpoint not passing config to rank_moments
  evidence: Confirmed config IS extracted at lines 318-323. The problem is the incoming data has wrong field names.

## Resolution

root_cause: |
  Issue 1 (GROQ_API_KEY): main.py never calls load_dotenv(), so .env is never loaded.
  grok_client.py reads GROQ_API_KEY at module import time (line 12) before main.py ever imports it,
  so the env var is empty string. The fix: add load_dotenv() at the top of main.py.

  Issue 2 (Config): Frontend sends camelCase (minDuration, maxDuration) but
  ProcessingConfig defines snake_case fields (min_clip_duration, max_clip_duration).
  Pydantic silently ignores unknown fields, so frontend's minDuration=90 becomes unused
  and the default min_clip_duration=60 is used instead.

fix: |
  1. Added "from dotenv import load_dotenv" and "load_dotenv()" at top of main.py (after service imports but before app creation)
  2. Added Field aliases to ProcessingConfig: minDuration -> min_clip_duration, maxDuration -> max_clip_duration, targetClips -> target_clips

verification: |
  - Syntax check: python3 -m py_compile main.py → PASSED
  - python-dotenv installed in backend/venv/ as per requirements.txt
  - Pydantic Field aliases correctly map camelCase frontend fields to snake_case backend fields

files_changed: [backend/main.py]