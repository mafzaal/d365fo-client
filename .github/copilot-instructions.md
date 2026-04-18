# Copilot instructions for `d365fo-client`

## Build, test, and lint commands

Use `uv` for local commands and dependency management.

```bash
# install dependencies
uv sync --dev

# full test suite
uv run pytest

# unit tests only
uv run pytest tests/unit

# integration tests only
uv run pytest tests/integration

# run one test file
uv run pytest tests/unit/test_cli.py

# run one test case
uv run pytest tests/unit/test_cli.py::TestCLIManager::test_config_list_empty

# run one integration file directly
uv run pytest tests/integration/test_sandbox_crud.py

# run sandbox integration suite through the project runner
uv run python tests/integration/test_runner.py sandbox --verbose

# run one sandbox integration file through the runner
uv run python tests/integration/test_runner.py sandbox --test test_sandbox_crud.py

# formatting and linting
uv run black --check .
uv run isort --check-only .
uv run ruff check .
uv run mypy src/

# build
uv build
```

Cross-platform wrappers exist and mirror the same workflows:

- Unix: `make dev`, `make quality-check`, `make test-unit`, `make build`
- PowerShell: `.\make.ps1 dev`, `.\make.ps1 quality-check`, `.\make.ps1 test-unit`, `.\make.ps1 build`

CI installs with `uv sync --all-extras`, runs `uv run pytest tests/ --cov=src/ --cov-report=xml`, and builds with `uv build`.

## High-level architecture

This repo has three connected surfaces that share the same core client:

1. **Python client**: `src/d365fo_client/client.py` defines `FOClient`, which composes auth, HTTP session management, CRUD helpers, metadata API helpers, and label operations. Metadata is initialized lazily and uses the V2 cache/search/sync stack under `src/d365fo_client/metadata_v2/`.
2. **CLI**: `src/d365fo_client/main.py` builds the argparse tree, and `src/d365fo_client/cli.py` routes commands through `CLIManager`, which resolves config and then runs the same `FOClient`.
3. **MCP server**: `src/d365fo_client/mcp/fastmcp_main.py` is the entry point, `fastmcp_server.py` assembles the FastMCP server, and tool implementations live in mixins under `src/d365fo_client/mcp/mixins/`. `D365FOClientManager` pools `FOClient` instances per profile for MCP use.

Configuration is shared between CLI and MCP:

- `FOClientConfig` in `models.py` is the base config model.
- `Profile` in `profiles.py` extends `FOClientConfig` so CLI/MCP profiles use the same core fields.
- `ConfigManager` and `ProfileManager` both read/write `~/.d365fo-client/config.yaml`.
- Environment-backed settings for MCP server startup live in `settings.py` via Pydantic settings.

## Key conventions

- **Prefer the V2 metadata stack.** `MetadataCacheV2` is the active cache implementation; new work should integrate with `metadata_v2/`, not older cache/sync modules.
- **Treat FastMCP mixins as the MCP extension point.** Add or change tools in `src/d365fo_client/mcp/mixins/`; `src/d365fo_client/mcp/tools/` is legacy.
- **Profiles are the shared config contract.** `Profile` inherits `FOClientConfig`, so new config fields usually belong in `FOClientConfig` first, then flow into profile serialization.
- **Config precedence matters.** The CLI resolves config in this order: command-line args -> environment variables -> saved profile -> defaults.
- **`credential_source=None` means Azure default credentials.** Legacy `client_id` / `client_secret` / `tenant_id` fields are migrated into `credential_source`; avoid adding new auth logic around the old fields.
- **Metadata access is cache-first by default.** `FOClient` lazily initializes metadata, prefers cache reads when enabled, and can trigger background sync when cache data is stale or missing.
- **MCP tools return dictionaries, including errors.** Shared tool behavior comes from `BaseToolsMixin._create_error_response()`, so keep tool outputs structured instead of returning JSON strings.
- **CLI output goes through `OutputFormatter`.** Supported formats are `json`, `table`, `csv`, and `yaml`; keep command handlers returning plain Python data that the formatter can render.
- **Example code should use the project defaults.** The repo consistently uses `D365FO_BASE_URL` with the One Box URL as the fallback default, and favors default Azure credentials unless explicit credentials are required.
- **D365 entity/action naming is significant.** For OData work, distinguish internal entity names from public entity / collection names, and respect action binding kinds (`Unbound`, `BoundToEntitySet`, `BoundToEntityInstance`) when constructing calls.
