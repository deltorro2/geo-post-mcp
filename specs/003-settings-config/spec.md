# Feature Specification: Settings Configuration

**Feature Branch**: `003-settings-config`
**Created**: 2026-02-23
**Status**: Draft
**Input**: User description: "The server should have settings file named geo-post-mcp-settings.json which stores database host, port, user, schema, list of tables allowed to access. The password of user should be stored in environment variable POSTGISMCPPASS (if not defined the password is considered as empty)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure Database Connection (Priority: P1)

An operator creates a settings file named
`geo-post-mcp-settings.json` to configure how the MCP server
connects to the database. The file contains the database host,
port, user, and schema. The server reads this file at startup
and uses it to establish a database connection. The database
password is provided via the `POSTGISMCPPASS` environment
variable for security; if the variable is not set, the
password defaults to empty.

**Why this priority**: Without database connection settings the
server cannot connect to any database, making all other
functionality impossible.

**Independent Test**: Can be tested by creating a settings file
with valid connection details, starting the server, and
verifying that it connects to the specified database. Delivers
value by enabling the server to reach the correct database.

**Acceptance Scenarios**:

1. **Given** a valid `geo-post-mcp-settings.json` file exists
   with host, port, user, and schema,
   **When** the server starts,
   **Then** it reads the settings and connects to the
   specified database using those values.

2. **Given** the `POSTGISMCPPASS` environment variable is set,
   **When** the server starts,
   **Then** it uses the variable's value as the database
   password.

3. **Given** the `POSTGISMCPPASS` environment variable is not
   set,
   **When** the server starts,
   **Then** it uses an empty string as the database password.

4. **Given** a settings file with incorrect connection details
   (e.g., wrong host or port),
   **When** the server starts,
   **Then** it reports a clear connection error identifying
   which setting is likely wrong.

---

### User Story 2 - Restrict Table Access (Priority: P2)

An operator specifies a list of allowed tables in the settings
file. The server only permits queries against these tables,
rejecting any query that references a table not on the list.
This allows the operator to control which data is exposed
through the MCP server.

**Why this priority**: Table access restriction is a critical
safety feature that prevents the MCP server from exposing
sensitive tables. It builds on the connection established in
User Story 1.

**Independent Test**: Can be tested by configuring an allowed
tables list, then attempting queries against both allowed and
disallowed tables. Delivers value by giving operators fine-
grained control over data exposure.

**Acceptance Scenarios**:

1. **Given** a settings file listing tables `["parcels",
   "buildings"]` as allowed,
   **When** a user queries `SELECT * FROM parcels`,
   **Then** the query executes successfully.

2. **Given** a settings file listing specific allowed tables,
   **When** a user queries a table not on the list,
   **Then** the server rejects the query with a clear error
   stating the table is not permitted.

3. **Given** a settings file with an empty allowed tables list,
   **When** a user attempts any query,
   **Then** the server rejects all queries since no tables
   are permitted.

4. **Given** a query that joins an allowed table with a
   disallowed table,
   **When** the query is submitted,
   **Then** the server rejects the query, identifying the
   disallowed table.

---

### User Story 3 - Validate Settings at Startup (Priority: P3)

When the server starts, it validates the settings file for
completeness and correctness before attempting to connect. If
required fields are missing, malformed, or the file itself is
absent, the server fails immediately with a clear, actionable
error message rather than starting in a broken state.

**Why this priority**: Startup validation prevents confusing
runtime failures by catching configuration errors early. It
supports all other stories by ensuring the server never runs
with invalid settings.

**Independent Test**: Can be tested by providing settings files
with various missing or malformed fields and verifying that
the server reports specific, helpful errors for each case.

**Acceptance Scenarios**:

1. **Given** the settings file is missing entirely,
   **When** the server starts,
   **Then** it fails with an error stating the settings file
   was not found and showing the expected file name and path.

2. **Given** the settings file is present but missing required
   fields (e.g., no host),
   **When** the server starts,
   **Then** it fails with an error listing each missing field.

3. **Given** the settings file contains a malformed value
   (e.g., port is a string instead of a number),
   **When** the server starts,
   **Then** it fails with an error identifying the field and
   the expected format.

4. **Given** the settings file is valid but contains an
   unrecognized field,
   **When** the server starts,
   **Then** it logs a warning about the unrecognized field
   but starts successfully.

---

### Edge Cases

- What happens when the settings file contains valid structure
  but the allowed tables list references tables that do not
  exist in the database? The system MUST start successfully
  but return clear errors when those tables are queried.
- What happens when the settings file is modified while the
  server is running? The system uses the settings read at
  startup; changes require a server restart.
- What happens when the settings file has incorrect file
  permissions (e.g., world-readable with a password nearby)?
  The system MUST log a warning if the file is readable by
  others beyond the owner.
- What happens when the schema specified in settings does not
  exist? The system MUST fail at startup with a clear error
  identifying the missing schema.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read configuration from a file named
  `geo-post-mcp-settings.json` at startup.
- **FR-002**: The settings file MUST contain the following
  fields: database host, database port, database user,
  database schema, and list of allowed tables.
- **FR-003**: System MUST read the database password from the
  `POSTGISMCPPASS` environment variable.
- **FR-004**: If the `POSTGISMCPPASS` environment variable is
  not defined, the system MUST use an empty string as the
  database password.
- **FR-005**: System MUST only allow queries against tables
  listed in the allowed tables configuration.
- **FR-006**: System MUST reject any query that references a
  table not in the allowed tables list, returning a clear
  error naming the disallowed table.
- **FR-007**: System MUST validate all required fields in the
  settings file at startup and fail with specific error
  messages for any missing or malformed fields.
- **FR-008**: System MUST fail at startup if the settings file
  is not found, reporting the expected file name and
  search path.
- **FR-009**: System MUST log a warning for unrecognized fields
  in the settings file but not fail.
- **FR-010**: System MUST log the loaded configuration at
  startup (excluding the password) for operational
  verification.

### Key Entities

- **Settings File**: A JSON file named
  `geo-post-mcp-settings.json` containing all server
  configuration. Attributes: database host, database port,
  database user, database schema, allowed tables list.
- **Allowed Table Entry**: A single table name in the allowed
  tables list. Used to validate queries before execution.

## Assumptions

- The settings file is located in the server's working
  directory or a well-known configuration path.
- The password is never stored in the settings file; the
  environment variable is the sole source.
- The allowed tables list uses fully qualified names within
  the configured schema (table names only, not
  schema-qualified).
- The settings file is read once at startup; runtime changes
  require a restart.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can configure the database connection
  by editing a single settings file without modifying
  application code.
- **SC-002**: 100% of queries against disallowed tables are
  rejected before reaching the database.
- **SC-003**: The server fails at startup with a clear,
  actionable error for every type of configuration problem
  (missing file, missing field, malformed value, unreachable
  database).
- **SC-004**: The database password never appears in log
  output or settings file.
- **SC-005**: An operator can configure and start the server
  in under 5 minutes on a new machine with a running
  database.
