# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses `uv` as the package manager.

### Running the Bot
```bash
uv run main.py
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_db.py

# Run with verbose output
uv run pytest -v
```

### Linting and Formatting
```bash
# Check code with ruff linter
uv run ruff check src tests

# Auto-fix linting issues
uv run ruff check --fix src tests

# Format code with ruff formatter
uv run ruff format src tests
```

### Type Checking
```bash
uv run mypy src
```

### Docker
```bash
# Build the local image (multistage: builder with gcc, slim python-alpine runtime)
docker build -t whitenz/next_train:<tag> .

# Start services
docker compose up -d

# View logs
docker compose logs -f backend

# Stop services
docker compose down
```

- **Never run `docker compose down -v` on the server** — it deletes `db_vol` with all data
- `data/*.sql` mounted into `/docker-entrypoint-initdb.d/` run only on an empty volume; existing data is never overwritten. Prod update: `docker compose pull && docker compose up -d`
- db healthcheck verifies the `schedule` table has rows (not just `pg_isready`), so backend (`depends_on: service_healthy`) never starts against an empty DB after a failed first-time populate
- DB port is published as `127.0.0.1:5433:5432` for running tests from the host only

## Architecture

This is a Telegram bot that provides next train information for the Yekaterinburg metro system.

### Core Components

**Bot Layer** (`src/bot.py`, `src/handlers.py`)
- Entry point: `main.py` calls `start_bot()` from `src/bot.py`
- Uses `python-telegram-bot` library with `Application` pattern
- Commands are registered via `COMMAND_HANDLERS` dict mapping commands to handler functions
- Main conversation flow: `/schedule` or `/add_favorite` → select station → select direction → display results

**Database Layer** (`src/db.py`, `src/models.py`)
- Uses SQLAlchemy 2.0 with ORM
- **Important**: Maintains both sync (`sync_engine`, `sync_session`) and async (`async_engine`, `async_session`) engines
  - Sync: Used for tests and simple queries
  - Async: Used for bot handlers and user operations
- Models: `Station`, `Schedule`, `BotUser`, `Favorite` (all dataclasses via `MappedAsDataclass`)
- Database functions accept session factory as default argument for testability
- **New functions:** `select_all_users()` and `delete_user()` for user management in broadcast feature

**Configuration** (`src/config.py`)
- Uses `pydantic-settings` with `BaseSettings`
- Loads from `.env.prod` then `.env.dev` — later files in the tuple override earlier ones (`.env.dev` wins where both define a variable)
- Python is constrained to `>=3.12,<3.14`: asyncpg 0.28 has no wheels and fails to build on Python 3.14
- Optional `PROXY_URL` routes both API calls and getUpdates polling through a proxy (hosts without direct Telegram access). Note: PTB's `.proxy()` alone does NOT cover long polling — `get_updates_proxy()` is applied too
- All settings accessed via singleton `settings` instance
- Key config: `MODE` (must be "test" for tests), `BOT_TOKEN`, database credentials

**Conversation Handlers** (`src/handlers.py`)
- Uses `ConversationHandler` for multi-step flows (station selection → direction selection)
- States defined in `bot_commands.py` module
- Inline keyboards for station/direction selection via `src/keyboards.py`
- **New:** `/broadcast` command for developer-only broadcasts to all users
  - Two states: WAITING_FOR_BROADCAST_TEXT → WAITING_FOR_BROADCAST_CONFIRM
  - Includes preview, confirmation, and rate limiting (27 msg/sec)
  - Automatically removes users who blocked the bot

### Key Implementation Details

**AsyncIO in Tests**
- Tests use `pytest` with `pytest-asyncio` in `asyncio_mode = "auto"`
- **Critical**: both `asyncio_default_test_loop_scope` and `asyncio_default_fixture_loop_scope` are set to `"session"` in `pyproject.toml` — tests AND async fixtures must share one event loop
- Mismatched loops cause "Future attached to a different loop" errors with SQLAlchemy's async engine (asyncpg pool is loop-bound)

**Database Initialization**
- Tests require the `.env.test` file (loaded by `pytest-dotenv` with `env_override_existing_values = 1`; see `.env.test.example`) and a PostgreSQL instance reachable at `localhost:5433` with an existing `next_train_test` database: `docker compose up --wait -d db`, then `docker exec next_train_db_cont psql -U postgres -c "CREATE DATABASE next_train_test;"`
- Test tables are created/dropped via `init_db` fixture in `tests/conftest.py`
- Populated with SQL from `data/populate_db.sql` via `populate_db` fixture
- Uses synchronous engine for setup, async for actual tests

**Time Handling**
- All times in `Asia/Yekaterinburg` timezone (configured via `TZ` env var)
- Metro operating hours: 5:30 AM - 12:30 AM next day (configured in `settings`)
- `Schedule.time_to_train` is a computed column property using PostgreSQL time arithmetic

**Logging**
- File-based logging to `logs/bot.log`
- Logs user commands via `@write_log` decorator in `src/decorators.py`
- `httpx` logger set to WARNING to reduce noise

## Environment Setup

Copy `.env.example` to `.env.dev` for local development:
- Set `MODE=dev` or `MODE=test` for testing
- Provide `BOT_TOKEN` from BotFather
- Set `DEVELOPER_TG_ID` for developer-only commands (e.g., `/download_log`)
- Configure database connection parameters

## Repository Conventions

- Plans and specs (`docs/plans/`, in `.gitignore`) are local-only and never committed; only reference files like `CLAUDE.md` go into git
- Comments in code are avoided: docstrings, constants and helper names carry the "why" instead