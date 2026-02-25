# Feature Specification: Settings File CLI Path Parameter

**Feature Branch**: `006-settings-cli-path`
**Created**: 2026-02-25
**Status**: Draft
**Input**: User description: "Currently the server looks for settings file geo-post-mcp-settings.json in the current folder but in most cases it will be not correct. We need to add command line parameter --sett <Path to geo-post-mcp-settings.json>. If this parameter wasn't provided from the command line the server still should look for this file in its current folder."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Specify Settings File Path via CLI (Priority: P1)

As a server operator, I want to provide an explicit path to the settings file when starting the server, so that the server can find its configuration regardless of the working directory it is launched from.

**Why this priority**: This is the core feature. Without it, the server fails to start in most deployment scenarios (e.g., Claude Desktop, systemd services, Docker) where the working directory differs from the project root.

**Independent Test**: Can be fully tested by starting the server with `--sett /path/to/settings.json` from any directory and verifying the server loads the correct configuration.

**Acceptance Scenarios**:

1. **Given** a valid settings file at `/home/user/config/geo-post-mcp-settings.json`, **When** the server is started with `--sett /home/user/config/geo-post-mcp-settings.json`, **Then** the server loads settings from that file and starts successfully.
2. **Given** a valid settings file at a relative path `../config/geo-post-mcp-settings.json`, **When** the server is started with `--sett ../config/geo-post-mcp-settings.json`, **Then** the server resolves the relative path and loads settings from that file.
3. **Given** an invalid path provided via `--sett /nonexistent/settings.json`, **When** the server is started, **Then** the server reports a clear error message indicating the file was not found at the specified path.

---

### User Story 2 - Default Fallback to Current Directory (Priority: P1)

As a server operator who runs the server from the project directory, I want the server to still find the settings file in the current folder when no `--sett` parameter is provided, so that existing workflows continue to work without changes.

**Why this priority**: Backward compatibility is essential — existing users and documentation rely on the current behavior.

**Independent Test**: Can be fully tested by placing `geo-post-mcp-settings.json` in the current directory, starting the server without `--sett`, and verifying the server loads settings from that file.

**Acceptance Scenarios**:

1. **Given** a settings file exists in the current working directory, **When** the server is started without the `--sett` parameter, **Then** the server loads settings from the current directory as before.
2. **Given** no settings file exists in the current directory and `--sett` is not provided, **When** the server is started, **Then** the server reports a clear error indicating the settings file was not found.

---

### Edge Cases

- What happens when `--sett` is provided but the value is an empty string? The server should report an error about missing or invalid file path.
- What happens when the file at the `--sett` path exists but contains invalid JSON? The server should report a parsing error that includes the file path.
- What happens when the file at the `--sett` path exists but is missing required fields? The server should report a validation error indicating which fields are missing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The server MUST accept an optional `--sett` command-line parameter that takes a file path as its value.
- **FR-002**: When `--sett` is provided, the server MUST use the specified path to load the settings file.
- **FR-003**: When `--sett` is not provided, the server MUST look for `geo-post-mcp-settings.json` in the current working directory (existing behavior preserved).
- **FR-004**: The `--sett` parameter MUST accept both absolute and relative file paths.
- **FR-005**: When the specified settings file does not exist, the server MUST display an error message that includes the full resolved path that was attempted.
- **FR-006**: The `--sett` parameter MUST work with all server transport modes (stdio, streamable-http).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Server can be started from any working directory by specifying the settings file path via `--sett`, and loads configuration successfully 100% of the time when the path is valid.
- **SC-002**: Existing workflows that rely on the settings file being in the current directory continue to work without any changes when `--sett` is not provided.
- **SC-003**: Error messages for missing or invalid settings files include the full file path that was attempted, enabling operators to diagnose configuration issues without additional debugging.

## Assumptions

- The `--sett` parameter name matches the user's request. An abbreviation of "settings" was chosen per the user's specification.
- The parameter is passed through the `fastmcp run` command's argument forwarding mechanism to the server script.
- The existing project-root-relative path resolution (added previously) will be replaced by this CLI parameter approach, as the CLI parameter is a more robust and explicit solution.
