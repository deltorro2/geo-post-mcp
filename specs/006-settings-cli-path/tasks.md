# Tasks: Settings File CLI Path Parameter

**Input**: Design documents from `/specs/006-settings-cli-path/`
**Prerequisites**: plan.md, spec.md, research.md

**Tests**: Not explicitly requested in specification. Test tasks omitted.

**Organization**: Tasks grouped by user story. Both stories are P1 and tightly coupled (same code path), so they share a single implementation phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new project setup needed — this is a modification to an existing project.

_No tasks in this phase._

---

## Phase 2: Foundational (Revert Previous Workaround)

**Purpose**: Restore `load_settings()` default to current-working-directory before adding CLI parameter support.

- [x] T001 Revert project-root-relative path resolution in src/config/settings.py back to `Path(SETTINGS_FILE_NAME)` default (undo the `Path(__file__).resolve().parent.parent.parent` workaround per research R-003)

**Checkpoint**: `load_settings()` defaults to looking in CWD again, matching FR-003.

---

## Phase 3: User Story 1 - Specify Settings File Path via CLI (Priority: P1) + User Story 2 - Default Fallback (Priority: P1) 🎯 MVP

**Goal**: Add `--sett` CLI parameter to specify settings file path. When omitted, fall back to current working directory.

**Independent Test (US1)**: Start server with `fastmcp run src/server.py -- --sett /path/to/settings.json` from any directory and verify correct settings loaded.

**Independent Test (US2)**: Start server without `--sett` from directory containing `geo-post-mcp-settings.json` and verify settings loaded.

### Implementation

- [x] T002 [US1] Add argument parsing with `argparse.ArgumentParser` and `parse_known_args()` in src/server.py to parse `--sett` parameter at module load time and pass the resolved `Path` to `load_settings()`
- [x] T003 [US1] Update `load_settings()` signature in src/config/settings.py to accept optional `settings_path: Path | None` (already exists) — verify it resolves relative paths via `.resolve()` before checking existence
- [x] T004 [US1] Add INFO-level structured log entry in src/server.py when `--sett` is used, logging the resolved path (per constitution principle IV: Log Coverage)
- [x] T005 [US1] Add type annotations to all new code and verify `mypy --strict` passes (per constitution principle II: Type Safety)

**Checkpoint**: Server starts with `--sett` from any directory, and without `--sett` from project directory. Error messages include full resolved path.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates to reflect the new CLI parameter.

- [x] T006 [P] Update Claude Desktop configuration example in README.md to use `--` separator with `--sett` parameter per research R-004
- [x] T007 [P] Update "Running the Server" section in README.md to document the `--sett` parameter for both stdio and streamable-http transport modes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: No dependencies — start immediately
- **User Stories (Phase 3)**: Depends on T001 completion
- **Polish (Phase 4)**: Depends on Phase 3 completion

### Within Phase 3

- T002 (argparse in server.py) and T003 (settings.py verification) can be done together but touch related code paths
- T004 (logging) depends on T002
- T005 (type check) depends on T002, T003, T004

### Parallel Opportunities

- T006 and T007 (README updates) can run in parallel with each other
- T006/T007 are independent files from T002-T005

---

## Implementation Strategy

### MVP (Recommended)

1. Complete T001 (revert workaround)
2. Complete T002-T005 (core implementation)
3. **STOP and VALIDATE**: Test with `fastmcp run src/server.py -- --sett geo-post-mcp-settings.json`
4. Complete T006-T007 (documentation)

---

## Notes

- Total tasks: 7
- Tasks per story: US1 = 4 implementation tasks, US2 = covered by T001 + T003 (same code path)
- Parallel opportunities: T006 + T007 (documentation)
- No new dependencies added (argparse is stdlib)
- Key research decision: FastMCP forwards args via `--` separator and `sys.argv` (R-001)
