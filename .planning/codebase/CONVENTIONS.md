# Coding Conventions

**Analysis Date:** 2026-05-23

## Naming Patterns

**Files:**
- PascalCase for classes/services: `TranscriptCache.ts`, `FileManager.ts`
- camelCase for utilities/helpers: `logger.ts`
- kebab-case for config files: `tsconfig.json`
- Suffix `.test.ts` for test files: `transcript-cache.test.ts`

**Classes:**
- PascalCase: `class TranscriptCache`, `class KnowledgeBase`
- Private members use `#` prefix or `private` keyword
- No `_` prefix for private fields (TypeScript convention)

**Functions/Variables:**
- camelCase: `getFileHash`, `createTaskDir`, `childLogger`
- Async functions prefixed with `handle` for handlers: `handleTranscribe`
- Tool definition exports suffixed with `ToolDef`: `transcribeToolDef`

**Interfaces/Types:**
- PascalCase: `TranscriptResult`, `CreateClipInput`, `KnowledgeFile`
- Suffix `Input` for input types: `TranscribeInput`, `SuggestClipsInput`
- Suffix `Result` for output types: `BatchClipsResult`
- Suffix `Event` for event types: `ProgressEvent`

**Constants:**
- UPPER_SNAKE_CASE for config constants: Not observed
- camelCase for module-level exports: `logger`, `childLogger`

**Enums/Typing:**
- Type unions as quoted strings: `type CaptionStyle = "branded" | "hormozi" | "karaoke" | "subtle"`

## Code Style

**Formatting:**
- Tool: Not explicitly configured (no .prettierrc, no eslint)
- Tab size: 2 spaces (inferred from TypeScript output)
- Semicolons: Yes (required for `fileManager.ts` line 52 `await rm(...)`)

**Linting:**
- Tool: ESLint configured in `frontend/` only (Next.js), not in `podcli/`
- Frontend uses `eslint-config-next`: `eslint: ^8.57.0`, `eslint-config-next: 14.2.0`

**TypeScript:**
- Strict mode enabled: `"strict": true` in `tsconfig.json`
- Target: ES2022, Module: ESNext, moduleResolution: bundler
- Declaration files generated: `"declaration": true`, `"declarationMap": true`
- ESM only (package.json `"type": "module"`)

**Import Organization:**
1. Node built-ins (`fs`, `path`, `os`, `crypto`)
2. Third-party packages (`winston`, `uuid`, `express`, `zod`)
3. Internal modules (`../services/`, `../handlers/`, `../config/`)
4. Type imports use `import type { ... }` for type-only imports

**Path Aliases:**
- No path aliases configured (relative imports used)
- Explicit `.js` extension for ESM: `import { TranscriptCache } from "./transcript-cache.js"`

## Error Handling

**Patterns:**
- Throws with descriptive messages: `throw new Error(\`File not found: ${filename}\`)`
- Error messages use template literals for context
- Async operations wrapped in try/catch for error recovery
- Errors re-thrown after logging where appropriate

**Error Propagation:**
```typescript
// In handlers - returns JSON error object for recoverable issues
catch (err: unknown) {
  const msg = err instanceof Error ? err.message : String(err);
  if (msg.includes("ECONNREFUSED")) {
    return JSON.stringify({ error: "Web UI not running..." });
  }
  throw err; // Fatal errors propagate
}
```

**Null Handling:**
- Null checks explicit: `if (cached) { ... }`
- Nullish coalescing: `input.model_size ?? "base"`
- Optional chaining: `data.words ?? []`

## Logging

**Framework:** Winston (`winston: ^3.17.0`)

**Pattern:**
- Module-level logger: `export const logger = winston.createLogger(...)`
- Child loggers per module: `const log = childLogger("suggest-clips")`
- Outputs to stderr (keeps stdout clean for MCP stdio)
- JSON mode via `PODCLI_LOG_JSON=1` env var
- Log levels: debug (dev), info (production)

**Key Files:**
- `src/utils/logger.ts` - Shared logger with child logger factory

## Comments

**JSDoc:**
- Used for public API documentation: `/** ... */`
- Descriptions explain purpose, not implementation
- `@param` for parameters, `@returns` when non-trivial

**Examples:**
```typescript
/**
 * Shared structured logger for the MCP server, handlers, and web UI.
 *
 * Writes to stderr so stdout stays clean for MCP stdio transport.
 * Use child loggers (logger.child({ mod: "suggest-clips" })) per module.
 */
export const logger = winston.createLogger(...);

/** Read all .md files concatenated — the main method used by MCP tools. */
async readAll(): Promise<string>
```

**Inline Comments:**
- Sparse - code should be self-documenting
- Explain non-obvious logic: `// default true` in `transcribe.handler.ts`

## Function Design

**Size:**
- Keep functions focused - single responsibility
- Large functions refactored into smaller helpers
- `formatResult()` in `transcribe.handler.ts` is a clear extraction

**Parameters:**
- Max 3-4 parameters before using options object
- Input types defined as interfaces: `TranscribeInput`
- Defaults via nullish coalescing: `input.model_size ?? "base"`

**Return Values:**
- Async handlers return `Promise<string>` (JSON string)
- Classes return typed results via methods
- Tool handlers return JSON-serialized results

## Module Design

**Exports:**
- Named exports preferred
- Classes exported directly: `export class KnowledgeBase`
- Tool definitions exported as objects: `export const transcribeToolDef = { ... }`
- Interfaces in separate `models/index.ts` barrel

**Barrel Files:**
- `src/models/index.ts` re-exports all types/interfaces
- `src/components/index.ts` (frontend)
- `src/lib/utils.ts` (frontend utilities)

**Class Structure:**
```typescript
export class ServiceClass {
  private dir = paths.knowledge;  // Dependency via closure
  async method(): Promise<void> { ... }
}
```

---

*Convention analysis: 2026-05-23*