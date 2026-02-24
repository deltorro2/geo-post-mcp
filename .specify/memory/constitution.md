<!--
Sync Impact Report
- Version change: N/A -> 1.0.0 (initial ratification)
- Added principles:
  - I. MCP Protocol Compliance
  - II. Type Safety
  - III. Syntactic Simplicity
  - IV. Log Coverage
- Added sections:
  - Core Principles (4 principles)
  - Technical Constraints
  - Development Workflow
  - Governance
- Templates requiring updates:
  - .specify/templates/plan-template.md - ✅ no updates needed (generic template)
  - .specify/templates/spec-template.md - ✅ no updates needed (generic template)
  - .specify/templates/tasks-template.md - ✅ no updates needed (generic template)
- Follow-up TODOs: none
-->

# Geo-Post MCP Constitution

## Core Principles

### I. MCP Protocol Compliance

All tool and resource definitions MUST strictly adhere to the
Model Context Protocol specification. Every MCP tool MUST declare
a complete JSON Schema for its input parameters. Resource URIs
MUST follow the `scheme://authority/path` convention defined by
MCP. Error responses MUST use MCP-standard error codes and
structured error content. No proprietary extensions to the
protocol are permitted without explicit amendment to this
constitution.

### II. Type Safety

All Python code MUST use type annotations on every function
signature (parameters and return types). Pydantic models MUST
be used for all data validation boundaries (MCP tool inputs,
database query results, configuration). The `Any` type MUST NOT
appear except when required by third-party library interfaces,
and each such usage MUST include a justifying comment.
`mypy --strict` or equivalent static analysis MUST pass with
zero errors before code is considered complete.

### III. Syntactic Simplicity

Code MUST favor straightforward, readable constructs over clever
or compact alternatives. Functions MUST do one thing and remain
short enough to understand without scrolling. Nesting depth
MUST NOT exceed 3 levels; extract helper functions instead.
Avoid metaclass magic, decorator stacking beyond two layers, and
dynamic attribute access unless strictly necessary. Prefer
explicit imports over wildcard imports. New abstractions MUST be
justified by at least two concrete use sites.

### IV. Log Coverage

All MCP tool invocations MUST be logged at INFO level with tool
name and a summary of input parameters (sensitive values
redacted). All database queries MUST be logged at DEBUG level
with query template and execution time. All errors MUST be
logged at ERROR level with full context (tool name, input
summary, exception type, message). Structured logging (JSON
format) MUST be used to enable machine parsing. Log levels MUST
follow: DEBUG for internals, INFO for operations, WARNING for
recoverable issues, ERROR for failures.

## Technical Constraints

- **Language**: Python 3.11+
- **MCP SDK**: FastMCP or official MCP Python SDK
- **Database**: PostgreSQL with PostGIS extension
- **ORM/Query**: Parameterized queries only; no string
  concatenation for SQL. Use asyncpg, psycopg, or SQLAlchemy
  with parameterized binds.
- **Input Validation**: All external inputs (MCP tool arguments,
  query parameters) MUST be validated via Pydantic before use.
- **Dependencies**: Minimize external dependencies. Each new
  dependency MUST be justified.

## Development Workflow

- Code reviews MUST verify compliance with all four Core
  Principles before approval.
- Every MCP tool MUST have at least one integration test that
  exercises the tool through the MCP protocol layer.
- Logging MUST be verified in integration tests (assert expected
  log entries are emitted).
- SQL injection vectors MUST be reviewed in every PR that
  touches database query code.

## Governance

This constitution is the authoritative source for project
standards. All code contributions, reviews, and architectural
decisions MUST comply with the principles defined above.

**Amendment procedure**: Any change to this constitution MUST be
documented with rationale, reviewed, and versioned according to
semantic versioning (MAJOR for principle removals/redefinitions,
MINOR for additions/expansions, PATCH for clarifications).

**Compliance review**: Each pull request MUST include a
self-assessment against the Core Principles. Reviewers MUST
verify principle compliance as a merge prerequisite.

**Version**: 1.0.0 | **Ratified**: 2026-02-23 | **Last Amended**: 2026-02-23
