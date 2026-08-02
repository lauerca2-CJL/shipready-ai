"""
Centralized configuration for ReviewBoard AI.

Responsibility:
    - Single source of truth for environment-derived settings: the Cursor
      API key, the default model ID, and any future tunables (timeouts,
      per-reviewer concurrency limits, etc.).
    - Every other module that needs a setting should import it from here
      rather than reading os.environ directly, so behavior stays consistent
      and easy to mock in tests.

Planned contents (not yet implemented):
    - A Settings object (likely pydantic-settings, or a lightweight
      dataclass loaded via python-dotenv) populated once from `.env` /
      environment variables.
    - CURSOR_API_KEY, REVIEWBOARD_MODEL, and — if reviewers ever need
      different models — per-reviewer model overrides.
    - A get_settings() accessor so callers don't construct Settings directly.

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: define Settings and a get_settings() accessor.
