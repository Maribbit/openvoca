# OpenVoca Backend

This is the backend component for OpenVoca, providing a REST API and acting as the bridge for LLM integrations (like local Ollama).

## Tech Stack
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Package & Environment Manager**: [uv](https://github.com/astral-sh/uv)
- **Database**: SQLite
- **ORM**: SQLModel

## Development Setup

```bash
# Sync dependencies (this creates the .venv automatically using uv)
uv sync

# Run the development server (auto-reloads on file changes)
uv run fastapi dev src/main.py
```

## Testing & TDD

We employ Test-Driven Development strictly. All business logic must be fully covered by tests before and during implementation.

- **Run Full Local Check**: `uv run ruff format --check .; uv run ruff check .; uv run pytest`
- **Run Tests**: `uv run pytest`
- **Frameworks**: We use pytest and httpx (for FastAPI's TestClient).
All tests are stored inside the `/tests` directory. Please execute checks frequently during the **Red-Green-Refactor** phase and always run the full local check before marking work as done.

## Architecture Guidelines
- **Project Structure**: All source code should be nested under `src`.
- **Typing**: Use standard Python type hinting. Leverage Pydantic and SQLModel classes for data verification and structure.
- **Dependencies**: Exclusively use `uv add <package>` to install dependencies; do not use raw pip.
