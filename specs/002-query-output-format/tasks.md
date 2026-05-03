# Tasks: Query Output Format

**Input**: Design documents from `/specs/002-query-output-format/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new packages needed. This phase is intentionally empty — all changes are to existing files.

*(No tasks)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add `output_format` parameter validation and pass-through logic that all user stories depend on.

- [x] T001 Add `output_format` parameter (type `str`, default `"text"`) to the `query()` function in `src/server.py`. Pass it through to `query_tool()`. Update the function's docstring to explain both formats: `"text"` (default, tabular data for textual answers) and `"geojson"` (GeoJSON FeatureCollection, recommended for drawing vector objects graphically in UI such as Leaflet maps).
- [x] T002 Add `output_format` parameter to `query_tool()` in `src/tools/query.py`. Add validation at the top of the function: if `output_format` is not `"text"` or `"geojson"`, raise `ValueError` with message listing valid options. No other logic changes yet — both formats currently return the existing text response.

**Checkpoint**: The `output_format` parameter is accepted and validated. Invalid values produce a clear error. Existing behavior is unchanged for `"text"` or omitted parameter.

---

## Phase 3: User Story 1 — GeoJSON Output for Map Visualization (Priority: P1)

**Goal**: When `output_format="geojson"`, return a Leaflet-compatible RFC 7946 GeoJSON FeatureCollection with geometry from the `geom` column and all other columns as Feature properties.

**Independent Test**: Call the query tool with `output_format="geojson"` on a spatial query and verify the response is a valid FeatureCollection with correct geometry and properties.

### Implementation for User Story 1

- [x] T003 [US1] Implement the `_to_geojson_feature_collection()` function in `src/tools/query.py`. This function takes a `QueryResult` (columns, rows, row_count, truncated) and returns a dict structured as a GeoJSON FeatureCollection. Logic: (a) find the index of the `geom` column in `columns` — if not found, raise `ValueError("GeoJSON output requires a column named 'geom' in the query results.")`; (b) for each row, read the `geom` column value (a GeoJSON string produced by ST_AsGeoJSON in T004), parse it via `json.loads()`, and use it as the Feature `geometry`; (c) all other columns become Feature `properties`; (d) handle null geometry (set `geometry: null`); (e) include `row_count` and, if truncated, `truncated` and `message` as top-level FeatureCollection fields.
- [x] T004 [US1] Modify the SQL execution in `query_tool()` in `src/tools/query.py`: when `output_format="geojson"`, before calling `execute_query()`, wrap the user's SQL in a subquery that converts the `geom` column to GeoJSON: `SELECT *, ST_AsGeoJSON(geom) AS geom FROM (SELECT * FROM ({sql}) AS __inner) AS __outer`. This replaces the raw WKB `geom` value with a GeoJSON string so that `_to_geojson_feature_collection()` can parse it directly from the `geom` column. The access control validation runs on the original SQL before wrapping.
- [x] T005 [US1] Add the conditional branch in `query_tool()` in `src/tools/query.py`: after `execute_query()` returns, if `output_format == "geojson"`, call `_to_geojson_feature_collection()` and return its result. Otherwise return the existing text format dict.

**Checkpoint**: Spatial queries with `output_format="geojson"` return a valid FeatureCollection. Queries without a `geom` column produce a clear error. Text format is unchanged.

---

## Phase 4: User Story 2 — Text Output as Default (Priority: P2)

**Goal**: Existing behavior is fully preserved when `output_format` is omitted or set to `"text"`.

**Independent Test**: Call the query tool without `output_format` and verify the response is identical to the pre-feature behavior.

### Implementation for User Story 2

- [x] T006 [US2] Verify backward compatibility in `src/tools/query.py`: confirm that `query_tool()` with `output_format="text"` (or when omitted, defaulting to `"text"`) returns the exact same dict structure as before (`columns`, `rows`, `row_count`, optional `truncated`/`message`). No code changes expected — this is a verification task to confirm T002 and T005 preserved the default path.

**Checkpoint**: All existing tests pass without modification. Omitting `output_format` produces identical results to pre-feature behavior.

---

## Phase 5: User Story 3 — Clear Tool Description (Priority: P3)

**Goal**: The query tool's MCP description clearly explains both output formats and recommends GeoJSON for map visualization.

**Independent Test**: List tools via MCP and verify the description mentions both formats with a recommendation for GeoJSON.

### Implementation for User Story 3

- [x] T007 [US3] Verify and finalize the query tool docstring in `src/server.py` (updated in T001): ensure the `output_format` parameter description clearly states: (a) `"text"` is the default for tabular data and textual answers; (b) `"geojson"` returns a GeoJSON FeatureCollection recommended for drawing vector objects graphically in UI (e.g., Leaflet maps); (c) GeoJSON requires the query to include a column named `geom`. Adjust wording if needed.

**Checkpoint**: MCP tool listing shows the updated description with both formats and the GeoJSON recommendation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Tests, regression check, and validation.

- [x] T008 [P] Add unit tests for `_to_geojson_feature_collection()` in `tests/unit/test_query_geojson.py`: test valid FeatureCollection structure with geometry and properties, test null geometry handling, test error when no `geom` column, test truncation metadata in response, test multiple rows produce multiple Features.
- [x] T009 [P] Add functional tests for GeoJSON output in `tests/functional/test_geo_query_tool.py`: add tests using the existing `mcp_client` fixture to call the query tool with `output_format="geojson"` on `test_parcels` (polygon) and `test_buildings` (point), verify valid FeatureCollection response with correct geometry types, verify error on query without `geom` column, verify invalid `output_format` produces error.
- [x] T010 Verify all existing tests still pass by running `python -m pytest tests/ -v` and run `mypy --strict src/tools/query.py` to confirm type safety. Fix any regressions or type errors.
- [x] T011 Run quickstart.md validation: invoke the query tool with both `output_format="text"` and `output_format="geojson"`, verify responses match the examples in `specs/002-query-output-format/quickstart.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: No dependencies — can start immediately
- **US1 (Phase 3)**: Depends on Phase 2 — needs validated `output_format` parameter
- **US2 (Phase 4)**: Depends on Phase 3 — verification that default path is preserved
- **US3 (Phase 5)**: Depends on Phase 2 — docstring finalization
- **Polish (Phase 6)**: Depends on Phases 3, 4, and 5

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2). Core feature.
- **User Story 2 (P2)**: Depends on User Story 1. Verification only.
- **User Story 3 (P3)**: Depends on Foundational (Phase 2). Can run in parallel with US1.

### Parallel Opportunities

- T007 (US3) can start as soon as Phase 2 completes, in parallel with US1
- T008 and T009 (Polish) can run in parallel (different test files)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001, T002)
2. Complete Phase 3: User Story 1 (T003–T005)
3. **STOP and VALIDATE**: Query with `output_format="geojson"` returns valid FeatureCollection
4. This alone delivers the core feature

### Incremental Delivery

1. Foundational → parameter accepted and validated
2. Add User Story 1 → GeoJSON output works (MVP)
3. Add User Story 2 → backward compatibility verified
4. Add User Story 3 → tool description finalized
5. Polish → tests, regression check, quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- T004 (SQL wrapping) is the key technical task — wraps user SQL in subquery for ST_AsGeoJSON conversion
- The `geom` column detection is by name convention (per spec clarification)
- Commit after each task or logical group
