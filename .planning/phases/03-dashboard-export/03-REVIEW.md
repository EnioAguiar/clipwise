---
phase: 03-dashboard-export
reviewed: 2026-05-23T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - backend/main.py
  - frontend/src/app/page.tsx
findings:
  critical: 0
  warning: 5
  info: 3
  total: 8
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-05-23
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed `backend/main.py` (441 lines) and `frontend/src/app/page.tsx` (598 lines) at standard depth. Found 5 warnings and 3 info-level issues. No critical security vulnerabilities or data loss risks were identified. The code generally follows good practices with proper error handling and environment variable usage for secrets.

## Warnings

### WR-01: Shadowed API_BASE Variable

**File:** `frontend/src/app/page.tsx:133`
**Issue:** `API_BASE` is redeclared inside the `sendToOpus` function, shadowing the module-level constant declared on line 44. While the inner declaration is used correctly for the fetch call, this creates confusion and could lead to bugs if the function is refactored.
**Fix:**
```typescript
// Remove the shadowed declaration at line 133
// The module-level API_BASE on line 44 will be used
const res = await fetch(`${API_BASE}/opus/send`, {
```

### WR-02: Debug Console Logs in Production Code

**File:** `frontend/src/app/page.tsx:223, 225, 294`
**Issue:** Three `console.log` statements with `[DEBUG]` prefixes remain in production code. These should be removed or replaced with proper logging infrastructure.
**Fix:**
```typescript
// Remove these lines:
console.log('[DEBUG] uploadRes status:', uploadRes.status)
console.log('[DEBUG] uploadData:', uploadData)
console.log('[DEBUG] processRes status:', processRes.status)
```

### WR-03: CORS Origin Hardcoded for Development

**File:** `backend/main.py:21`
**Issue:** `allow_origins=["http://localhost:3000"]` is hardcoded. This will block production frontend domains. Should be read from environment configuration.
**Fix:**
```python
allow_origins=[os.getenv("CORS_ORIGIN", "http://localhost:3000")],
```

### WR-04: Opus API Error Details Exposed to Client

**File:** `backend/main.py:409`
**Issue:** When Opus API returns an error, `response.text` is included in the HTTPException detail. This could leak Opus API internal error messages to the client.
**Fix:**
```python
if response.status_code != 200:
    raise HTTPException(
        status_code=502,
        detail="Opus API request failed"
    )
```

### WR-05: LocalStorage Configuration without Encryption

**File:** `frontend/src/app/page.tsx:75`
**Issue:** Processing configuration is stored in localStorage as plain JSON. If the config contains any sensitive values in the future, they would be persisted in plain text.
**Fix:** If sensitive data may be added to config later, consider using encrypted storage or a secure HTTP-only cookie for auth tokens.

## Info

### IN-01: Inconsistent Logging Levels

**File:** `backend/main.py:74, 232, 244, 252, etc.`
**Issue:** `logger.warning()` is used for informational messages like "Starting transcription..." and "Starting energy extraction...". Warning level should indicate actual warning conditions. Consider using `logger.info()` for progress messages.
**Fix:** Replace `logger.warning` with `logger.info` for routine progress logging.

### IN-02: Unused Import

**File:** `backend/main.py:6`
**Issue:** `import httpx` is used on line 392 but `httpx` is also imported at the module level (line 6). Verify if the module-level import is used elsewhere or if the inline import (line 392) can be removed.
**Fix:** Check if httpx is used anywhere else at module level; if not, remove the inline import on line 392.

### IN-03: Redundant Variable Declaration

**File:** `frontend/src/app/page.tsx:195`
**Issue:** `videoId` is declared with `let` but the variable on line 232 uses the same name, creating confusion. The inner assignment on line 232 is in a different scope, but the shadowing is unnecessary.
**Fix:** Consider renaming the outer scoped variable to avoid confusion:
```typescript
let videoIdFromUpload: string
// ...
videoIdFromUpload = uploadData.file_id
```

---

_Reviewed: 2026-05-23_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
