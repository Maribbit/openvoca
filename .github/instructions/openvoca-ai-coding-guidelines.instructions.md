---
description: Read before writing any code for the OpenVoca project. These guidelines are mandatory for all AI-generated code contributions.
applyTo: "**/*"
---

# OpenVoca AI Coding Guidelines

As an AI programming assistant working on this project, please adhere to the following VERY STRICT guidelines:

## 1. Documentation & Comments

- **English Only**: ALL code comments, docstrings, inline explanations, and commit messages MUST be written in English. Do not write Chinese comments in the codebase.
- **Conciseness**: Keep comments brief and focus on the "why" rather than the "how". Avoid redundant comments for obvious code.
- **No File Headers**: Do not add file-level boilerplate comments (e.g. author tags, creation dates) unless specifically requested.

## 2. Code Style & Architecture

- **Vue 3 (Frontend)**:
  - ALWAYS use <script setup lang="ts"> and the Composition API.
  - Rely on Tailwind v4 utility classes and avoid writing custom CSS in <style> blocks unless absolutely necessary for animations or complex pseudo-elements.
  - Follow our global Zen Mode aesthetic: 'paper' backgrounds and 'ink' text.

- **Python (Backend)**:
  - Strongly type all Python function arguments and return signatures using Python 3.12+ type hints.
  - Leverage Pydantic/SQLModel strictly.
  - Prefer explicit structural imports over wildcard imports.

## 3. Toolchain Compliance

- Never recommend npm or yarn. Only use pnpm for frontend dependency management.
- Never recommend raw pip. Only use uv for python environment and dependency management.
- Never create commits, amend commits, or push to remote unless the user explicitly asks for it.

## 4. Testing & Specs (Test-Driven Development)

- **Specs-First**: Always refer to the acceptance criteria (AC) in `docs/specs/` before writing tests or code. Local OpenVoca uses these Chinese specification files as the source of truth for business logic.
- **Traceability**: When writing a new test, MUST inject an inline comment (`# Covers: AC-XXX` for Python, `// Covers: AC-XXX` for TypeScript) on the line immediately preceding the test definition.
- **Red-Green-Refactor**: ALWAYS follow Test-Driven Development. When asked to implement complex logic, FIRST write failing tests mapped to ACs (Red), THEN implement the code to pass it (Green), and finally optimize (Refactor). Do not generate massive chunks of business logic without tests.
- **Frontend Stack**: Use vitest and @vue/test-utils.
- **Backend Stack**: Use pytest and httpx (TestClient).
- **Mandatory Check Commands**:
  - Traceability: `python scripts/check_traceability.py`
  - Frontend: `pnpm run check`
  - Backend: `uv run ruff format --check .; uv run ruff check .; uv run pytest`
  - Workspace (VS Code task): `✅ Check OpenVoca (All)`
- **Completion Rule**: Before claiming implementation is finished, run the relevant check command(s) and verify they pass.

## Guidelines

- **[Concept & Specs](../../docs/specs/README.md)**: Details the core mechanic and test mappings.
- **[Toolchain](../../design/Toolchain.md)**: Dependency management and environments.
