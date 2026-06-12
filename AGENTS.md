# AGENTS.md

These instructions apply to this repository.

- Keep generated changes small and reviewable by maintainers.
- When applying Slophammer standards, follow the upstream agent entrypoint:
  https://github.com/osolmaz/slophammer/blob/main/docs/AGENT_ENTRYPOINT.md
- Preserve the public package API unless the change is explicitly scoped as breaking.
- Add or update tests when changing behavior.
- Run `uv run ruff format --check .`, `uv run ruff check .`, `uv run ty check manim_voiceover`, `uv run mypy`, `uv run pytest --cov=manim_voiceover --cov-fail-under=85`, `uvx slophammer-py@0.3.0 dry .`, `uv run mutmut run`, `uv run python scripts/check_mutmut_results.py`, `uv run pip-audit`, `uvx slophammer-py@0.3.0 check .`, and `uvx slophammer-py@0.3.0 check . --execute` before submitting a change.
- Public functions and meaningful helpers must stay annotated and pass Ruff `ANN`, ty, and strict mypy.
- Keep `Any`, casts, and import ignores isolated to external-library boundaries with a clear reason.
- Use the existing project style and avoid unrelated formatting churn.
