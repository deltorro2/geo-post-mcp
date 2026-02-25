# Research: Settings File CLI Path Parameter

## R-001: FastMCP CLI Argument Forwarding

**Decision**: Use `sys.argv` parsing via `argparse` in `server.py` at module load time.

**Rationale**: FastMCP 3.x `fastmcp run` command supports forwarding extra CLI arguments to the server script via the `--` separator:
```
fastmcp run src/server.py -- --sett /path/to/settings.json
```
Internally, FastMCP uses a `with_argv()` context manager that temporarily sets `sys.argv` to the forwarded arguments before importing the server module. This means standard `argparse` or direct `sys.argv` access works during module import/execution.

**Alternatives considered**:
- Environment variable for path: Rejected — user explicitly requested a CLI parameter `--sett`.
- Custom FastMCP configuration: Rejected — FastMCP doesn't have built-in settings-path support; `sys.argv` forwarding is the intended mechanism.

## R-002: Argument Parsing Approach

**Decision**: Use `argparse` with `parse_known_args()` for robustness.

**Rationale**: `parse_known_args()` parses only the known `--sett` argument and ignores any other arguments that FastMCP or future extensions may add. This avoids fragile `sys.argv` index-based access and provides automatic help text and error handling.

**Alternatives considered**:
- Direct `sys.argv` indexing: Rejected — brittle, no validation, no help text.
- `click` library: Rejected — unnecessary dependency for a single optional argument.

## R-003: Revert Project-Root Fallback

**Decision**: Revert the previously added project-root-relative path resolution in `settings.py` back to current-working-directory default.

**Rationale**: The `--sett` parameter provides a more explicit and reliable mechanism. The project-root fallback (using `Path(__file__).resolve().parent.parent.parent`) was a workaround that should be replaced by the CLI parameter. Per the spec (FR-003), the default behavior when `--sett` is not provided should be to look in the current working directory.

## R-004: Claude Desktop Configuration Update

**Decision**: Update README documentation to show the `--` separator syntax for passing `--sett` to the server via Claude Desktop config.

**Rationale**: Claude Desktop config `args` array needs to include `--`, `--sett`, and the path as separate elements:
```json
"args": ["run", "src/server.py", "--", "--sett", "/path/to/settings.json"]
```
