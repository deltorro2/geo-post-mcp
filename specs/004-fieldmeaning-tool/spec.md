# Feature Specification: Field Meaning Tool

**Feature Branch**: `004-fieldmeaning-tool`
**Created**: 2026-02-23
**Status**: Draft
**Input**: User description: "The MCP should have the additional tool named 'fieldmeaning' which receives the name of table and returns the textual meaning of each field based on comments in the schema of this table."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Retrieve Field Meanings for a Table (Priority: P1)

An AI assistant user calls the `fieldmeaning` MCP tool with a
table name. The tool queries the database schema for column
comments on that table and returns a structured list mapping
each column name to its human-readable description. This
allows the assistant to understand what each field represents
before writing queries.

**Why this priority**: This is the entire purpose of the tool.
Without it, the feature has no value.

**Independent Test**: Can be tested by creating a table with
comments on its columns, invoking the `fieldmeaning` tool with
that table name, and verifying the returned descriptions match
the schema comments.

**Acceptance Scenarios**:

1. **Given** a table `parcels` exists with comments on all its
   columns (e.g., column `gid` has comment "Unique parcel
   identifier"),
   **When** the user calls `fieldmeaning` with table name
   `parcels`,
   **Then** the tool returns a list of all columns with their
   names and comment text.

2. **Given** a table where some columns have comments and
   others do not,
   **When** the user calls `fieldmeaning` with that table name,
   **Then** columns with comments show their description, and
   columns without comments are included with an indication
   that no description is available.

3. **Given** a table that exists but has no column comments
   at all,
   **When** the user calls `fieldmeaning` with that table name,
   **Then** the tool returns all column names, each marked as
   having no description available.

4. **Given** a table name that does not exist in the database,
   **When** the user calls `fieldmeaning` with that name,
   **Then** the tool returns a clear error stating the table
   was not found.

---

### User Story 2 - Respect Table Access Restrictions (Priority: P2)

When the `fieldmeaning` tool is called with a table name, the
system checks whether that table is in the allowed tables list
(from the settings configuration). If the table is not
permitted, the tool rejects the request, consistent with how
query execution handles disallowed tables.

**Why this priority**: Access control consistency is critical
for security. The `fieldmeaning` tool MUST NOT expose schema
information for tables the operator has restricted.

**Independent Test**: Can be tested by configuring an allowed
tables list, then calling `fieldmeaning` for both an allowed
and a disallowed table, verifying the disallowed request is
rejected.

**Acceptance Scenarios**:

1. **Given** the settings allow access to table `parcels`,
   **When** the user calls `fieldmeaning` with table name
   `parcels`,
   **Then** the tool returns the field meanings successfully.

2. **Given** the settings do not include table `users` in the
   allowed list,
   **When** the user calls `fieldmeaning` with table name
   `users`,
   **Then** the tool rejects the request with an error stating
   the table is not permitted.

---

### Edge Cases

- What happens when the table name contains special characters
  or SQL injection attempts? The tool MUST use parameterized
  queries for the schema lookup and never interpolate the table
  name into raw SQL.
- What happens when the database connection is lost while
  retrieving comments? The tool MUST return a connection error
  consistent with other tools in the server.
- What happens when the table has hundreds of columns? The tool
  MUST return all columns without truncation (field metadata
  is always a bounded, manageable size).
- What happens when a column comment contains very long text?
  The tool MUST return the full comment text without
  truncation.
- What happens when a schema-qualified name is provided
  (e.g., `public.parcels`)? The tool MUST reject the input
  with an error indicating that only bare table names are
  accepted.

## Clarifications

### Session 2026-02-23

- Q: Should the tool include spatial metadata (geometry type, SRID, dimensions) for PostGIS columns? → A: No — return comments and data type only; keep the tool narrowly focused.
- Q: Should the tool accept schema-qualified table names or bare names only? → A: Bare table names only — always resolve against the configured schema.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose an MCP tool named
  `fieldmeaning` that accepts a single required parameter:
  a bare table name (not schema-qualified). The table is
  resolved against the schema configured in the settings file.
- **FR-002**: The `fieldmeaning` tool MUST return, for each
  column in the specified table, the column name and its
  schema comment text.
- **FR-003**: For columns that have no schema comment, the
  tool MUST include the column in the result with a clear
  indicator that no description is available (e.g., null or
  an explicit "No description" marker).
- **FR-004**: The tool MUST return an error when the specified
  table does not exist in the database.
- **FR-005**: The tool MUST enforce the same table access
  restrictions as query execution — if a table is not in the
  allowed tables list, the tool MUST reject the request.
- **FR-006**: The tool MUST include the column data type
  alongside each field's name and description to provide
  complete context.
- **FR-007**: The `fieldmeaning` tool MUST have a complete
  JSON Schema definition for its input parameter (table name)
  in the MCP tool catalog.
- **FR-008**: The tool MUST log each invocation with the
  requested table name and result count.

### Key Entities

- **Field Meaning Entry**: A single column's metadata as
  returned by the tool. Attributes: column name, data type,
  description text (from schema comment), indicator for
  missing description.

## Assumptions

- Column comments are set by database administrators using
  standard comment-on-column functionality and are the
  authoritative source of field meaning.
- The tool operates within the schema configured in the
  settings file.
- The tool returns results for all columns in the table,
  not a subset.
- Column ordering in the result follows the ordinal position
  defined in the database schema.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can retrieve human-readable field
  descriptions for any allowed table in a single tool call.
- **SC-002**: 100% of columns in a table are included in the
  result, whether or not they have comments.
- **SC-003**: Requests for disallowed tables are rejected
  100% of the time, consistent with query access controls.
- **SC-004**: Users can understand the meaning of unfamiliar
  database fields without needing external documentation or
  direct database access.
