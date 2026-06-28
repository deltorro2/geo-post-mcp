# Feature Specification: Upsert Metadata Tool

**Feature Branch**: `003-upsert-metadata`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "Add the new tool - upsert_metadata. The tool receives 4 parameters: table name, id, newkey, newvalue. Calling this tool allows to add the new json key/value into the 'metadata' field of the relevant table. If newkey already exists in the metadata his value will be replaced by newvalue. Pay attention the current architecture of the MCP doesnt allow any SQL requests except data read - this tool should be allowed to perform the required changes."

## Clarifications

### Session 2026-06-28

- Q: How should `newvalue` be typed when stored in metadata (string vs. JSON)? → A: Auto-detect — if `newvalue` is valid JSON (number, boolean, null, object, array), store it as that typed value; otherwise store it as a string.
- Q: Should the write capability be gated behind an opt-in setting, or always enabled? → A: Always enabled — no config flag. The write capability is permanently scoped to the `upsert_metadata` tool only, and only to the `metadata` field of eligible tables; all other tools and fields remain read-only.
- Q: Which column identifies the record to update? → A: A column literally named `id`. Tables without an `id` column are ineligible.
- Note (2026-06-28, from planning input): The `id` column is always a `bigint` and always the primary key of the table; the `id` tool parameter is an integer, bound directly. Record presence/uniqueness is therefore guaranteed by the primary key.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add a new key to a record's metadata (Priority: P1)

A user (via an MCP client) wants to enrich an existing database record by attaching a new piece of information to it. They identify the record by its table and id, then supply a key and a value to store under the record's `metadata` field.

**Why this priority**: This is the core capability of the feature — without the ability to add a new key/value, the tool delivers no value. It is the minimum viable slice.

**Independent Test**: Can be fully tested by calling the tool with a table, an existing record id, a brand-new key, and a value, then reading the record back and confirming the new key/value is present in `metadata` while previously existing keys remain untouched.

**Acceptance Scenarios**:

1. **Given** a record whose `metadata` does not contain the key `"source"`, **When** the user calls the tool with that record's table, id, key `"source"`, and value `"survey-2026"`, **Then** the record's `metadata` contains `"source": "survey-2026"` and all previously existing keys are unchanged.
2. **Given** a record whose `metadata` is empty or unset, **When** the user calls the tool with a new key/value, **Then** the record's `metadata` is created/populated containing exactly that key/value.

---

### User Story 2 - Replace the value of an existing metadata key (Priority: P1)

A user wants to correct or update information already stored under a known key in a record's `metadata`. They supply the same key with a new value, expecting the old value to be overwritten.

**Why this priority**: The "upsert" semantics (update-or-insert) are central to the feature name and the stated requirement that an existing key's value must be replaced. Equal in importance to inserting a new key.

**Independent Test**: Can be tested by calling the tool twice for the same record/key with different values, then confirming only the most recent value is stored.

**Acceptance Scenarios**:

1. **Given** a record whose `metadata` already contains `"status": "draft"`, **When** the user calls the tool with key `"status"` and value `"published"`, **Then** `metadata` contains `"status": "published"` and no duplicate `"status"` entry exists.
2. **Given** a record with several existing metadata keys, **When** the user replaces the value of one key, **Then** the other keys retain their original values.

---

### User Story 3 - Safe handling of invalid requests (Priority: P2)

A user calls the tool with a record id that does not exist, a table that has no `metadata` field, or a table that is not permitted for access. The tool must reject the request clearly without altering any data.

**Why this priority**: Protecting data integrity and giving clear feedback is important, but the feature can be demonstrated and deliver value without it. It strengthens the core capability rather than enabling it.

**Independent Test**: Can be tested by calling the tool with a non-existent id, a table lacking a `metadata` field, and a disallowed table, then confirming each call returns a clear error and leaves all data unchanged.

**Acceptance Scenarios**:

1. **Given** an id that matches no record in the target table, **When** the user calls the tool, **Then** the tool reports that no record was found and makes no changes.
2. **Given** a table that does not have a `metadata` field, **When** the user calls the tool, **Then** the tool reports the table is not eligible and makes no changes.
3. **Given** a table that is outside the configured set of accessible tables, **When** the user calls the tool, **Then** the tool denies the request consistent with the existing access-control rules.

---

### Edge Cases

- What happens when the target record's `metadata` is `NULL` or absent? → A new metadata object containing the supplied key/value is created.
- What happens when `newvalue` is an empty string? → The key is stored with an empty-string value (a valid update, distinct from removing the key).
- What happens when more than one record shares the supplied id? → See Assumptions; the expectation is that id uniquely identifies a single record.
- How does the system handle a `newkey` or `newvalue` containing characters that could be misinterpreted (e.g., quotes, braces)? → The values are stored verbatim as data, with no possibility of altering other keys or other records.
- What happens when the same key is upserted concurrently by two callers? → The last write wins; no partial/corrupted metadata results.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose a tool named `upsert_metadata` that accepts four inputs: table name, record id, key, and value.
- **FR-002**: System MUST add the supplied key/value pair into the `metadata` field of the record identified by the given table and id.
- **FR-003**: System MUST replace the existing value when the supplied key already exists in the record's `metadata`, without creating a duplicate key.
- **FR-004**: System MUST preserve all other existing keys and values in the record's `metadata` when adding or replacing a key.
- **FR-005**: System MUST create the metadata object when the target record has no existing `metadata` (e.g., null or empty), populating it with the supplied key/value.
- **FR-006**: System MUST permit this tool to perform the write operation even though the platform otherwise restricts operations to read-only data access. The write capability is always enabled (no configuration flag) and MUST be permanently scoped to: (a) the `upsert_metadata` tool only, and (b) the `metadata` field only. It MUST NOT enable writes to any other field, nor arbitrary write operations through any other tool.
- **FR-007**: System MUST apply the existing table access-control rules so the tool can only modify tables the caller is already permitted to access.
- **FR-008**: System MUST report a clear, actionable result indicating success or the reason for failure (e.g., record not found, table ineligible, access denied).
- **FR-009**: System MUST make no changes to any data when a request is rejected or fails validation.
- **FR-010**: System MUST treat the supplied key and value strictly as data, ensuring they cannot modify keys other than the supplied one, other records, or other fields.
- **FR-011**: System MUST limit the change to exactly one record (the one matching the supplied id) per call.
- **FR-012**: System MUST interpret `newvalue` by auto-detecting its type: if `newvalue` is valid JSON (number, boolean, null, object, or array), it MUST be stored as that typed JSON value; otherwise it MUST be stored as a JSON string. Example: `newvalue="42"` stores the number `42`; `newvalue="draft"` stores the string `"draft"`.

### Key Entities *(include if feature involves data)*

- **Record**: A single row in a database table, uniquely identified by its `id`. Each eligible record carries a `metadata` field that holds a collection of key/value pairs.
- **Metadata**: A structured collection of key/value pairs attached to a record. Keys are unique within a record's metadata; values are associated data.
- **Upsert request**: The combination of table name, record id, key, and value that describes the single change to apply.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can add a new key/value to an existing record's metadata in a single tool call, and reading the record afterward shows the new pair present.
- **SC-002**: Re-calling the tool with an existing key replaces its value in 100% of cases, with zero duplicate keys produced.
- **SC-003**: 100% of calls that target a non-existent record, an ineligible table, or a disallowed table result in no data change and a clear error message.
- **SC-004**: Adding or replacing one key never alters any other key, record, or field — verifiable by comparing the full record before and after the call.
- **SC-005**: The platform's read-only guarantee for all other tools remains intact: no tool other than `upsert_metadata` can perform a data write after this feature ships.

## Assumptions

- **Record identifier**: The `id` parameter is matched against the table's `id` column, which is always a `bigint` and always the primary key. It therefore uniquely identifies exactly one record, and the tool affects exactly one record per call. The `id` parameter is an integer.
- **Metadata field name and type**: The target field is literally named `metadata` and holds structured key/value data (a JSON-like object). Tables without such a field are ineligible.
- **Value type**: `newvalue` is type-detected (see FR-012) — valid JSON is stored as its native JSON type, otherwise it is stored as a JSON string.
- **Access control**: The same configured set of accessible tables/schemas that governs the existing read tools also governs which tables `upsert_metadata` may modify.
- **Audit/logging**: Tool invocations are logged consistent with the existing logging behavior of other tools; no new audit mechanism is introduced by this feature.
- **No deletion**: Removing a key from metadata is out of scope; this tool only adds or replaces.
