# Testing Patterns

**Analysis Date:** 2026-05-23

## Test Framework

**Runner:**
- Vitest (`vitest: ^2.1.9`)
- Config: Not found (uses Vitest defaults)
- Run commands in `package.json`:
  - `test` → `vitest run` (single run)
  - `test:watch` → `vitest` (watch mode)

**Assertion Library:**
- Vitest built-in (`expect`)

**Mocking:**
- Vitest built-in mocking (native ESM mocks via `await import()`)

## Test File Organization

**Location:**
- Co-located with source files
- Sibling naming: `transcript-cache.ts` → `transcript-cache.test.ts`

**Structure:**
```
src/services/
├── transcript-cache.ts
├── transcript-cache.test.ts
├── knowledge-base.ts
├── knowledge-base.test.ts
├── file-manager.ts
├── file-manager.test.ts
├── asset-manager.ts
├── asset-manager.test.ts
└── clips-history.ts
    └── clips-history.test.ts
```

## Test Structure

**Suite Organization:**
```typescript
import { describe, it, expect, beforeEach } from "vitest";
import { mkdtempSync, writeFileSync, rmSync, mkdirSync } from "fs";
import { tmpdir } from "os";
import { join } from "path";

// Setup temp directory with env vars
const tmp = mkdtempSync(join(tmpdir(), "podcli-cache-test-"));
process.env.PODCLI_HOME = tmp;
process.env.PODCLI_DATA = tmp;

// Dynamic import for ESM
const { TranscriptCache } = await import("./transcript-cache.js");

describe("TranscriptCache", () => {
  let cache: InstanceType<typeof TranscriptCache>;

  beforeEach(() => {
    rmSync(join(tmp, "cache"), { recursive: true, force: true });
    mkdirSync(join(tmp, "cache", "transcripts"), { recursive: true });
    cache = new TranscriptCache();
  });

  it("returns null for an uncached file", async () => {
    // Test content
  });
});
```

**Patterns:**
- `beforeEach` for setup (clean state)
- `describe` blocks for class/feature grouping
- `it` or `test` for individual cases
- Dynamic imports (`await import()`) for ESM modules

## Mocking

**Framework:** Vitest native mocking

**Patterns:**
```typescript
// No explicit mock() calls - uses real implementations
// Temp filesystem for isolation
const tmp = mkdtempSync(join(tmpdir(), "podcli-cache-test-"));
process.env.PODCLI_HOME = tmp;

// Fake data creation
function makeFakeVideo(name: string, content: string): string {
  const p = join(tmp, name);
  writeFileSync(p, content);
  return p;
}
```

**What to Mock:**
- Environment variables (set via `process.env.X = value`)
- No mocking of internal classes - tests use real implementations
- File system isolated via temp directories

**What NOT to Mock:**
- Service classes themselves (test real behavior)
- Winston logger (used directly in tests)
- TypeScript types/interfaces (structural)

## Fixtures and Factories

**Test Data:**
```typescript
// Fake transcript fixture
const fakeTranscript: TranscriptResult = {
  transcript: "hello world",
  segments: [],
  words: [
    { word: "hello", start: 0, end: 0.5, confidence: 0.99 },
    { word: "world", start: 0.5, end: 1.0, confidence: 0.99 },
  ],
  duration: 1.0,
  language: "en",
  speakers: { num_speakers: 0, speakers: {} },
  speaker_segments: [],
};

// Factory pattern for files
function makeFakeVideo(name: string, content: string): string {
  const p = join(tmp, name);
  writeFileSync(p, content);
  return p;
}
```

**Location:**
- Inline in each test file (no shared fixtures directory)
- Temp directories created per test suite

## Coverage

**Requirements:** None explicitly enforced

**View Coverage:** Not configured (no `vitest --coverage`)

## Test Types

**Unit Tests:**
- Service class tests: `TranscriptCache`, `KnowledgeBase`, `FileManager`, `AssetManager`
- Tests real behavior with temp filesystem
- No external dependencies (network, database)

**Integration Tests:**
- Not separately identified
- File operations tested against real filesystem

**E2E Tests:**
- Not present in `podcli/` (frontend may have separate setup)

## Common Patterns

**Async Testing:**
```typescript
it("set then get round-trips the transcript", async () => {
  const file = makeFakeVideo("cached.mp4", "stable content here");
  await cache.set(file, fakeTranscript);
  const loaded = await cache.get(file);
  expect(loaded).not.toBeNull();
  expect(loaded?.transcript).toBe("hello world");
});
```

**Error Testing:**
```typescript
it("readFile throws for missing files", async () => {
  await expect(kb.readFile("ghost.md")).rejects.toThrow(/File not found/);
});

it("rejects registration of missing files", async () => {
  await expect(
    manager.register("ghost", "/nonexistent/file.png", "logo"),
  ).rejects.toThrow(/File not found/);
});
```

**Idempotency Testing:**
```typescript
it("ensureDirectories is idempotent", async () => {
  await fm.ensureDirectories();
  await expect(fm.ensureDirectories()).resolves.toBeUndefined();
});
```

## Observed Test Files

| File | Lines | Description |
|------|-------|-------------|
| `src/utils/logger.test.ts` | - | Logger utility tests |
| `src/services/transcript-cache.test.ts` | 78 | Cache get/set/hash/corruption |
| `src/services/knowledge-base.test.ts` | 89 | File CRUD, list, readAll |
| `src/services/file-manager.test.ts` | 116 | Dir creation, task dirs, cleanup |
| `src/services/clips-history.test.ts` | - | Clip history operations |
| `src/services/asset-manager.test.ts` | 72 | Asset register/list/resolve |

---

*Testing analysis: 2026-05-23*