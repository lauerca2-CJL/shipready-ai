"""
Centralized configuration for ShipReady AI.

Responsibility:
    Single source of truth for tunable settings that would otherwise be
    hardcoded inside individual modules. Every other module that needs a
    setting should import it from here rather than reading os.environ (or
    hardcoding a literal) directly, so behavior stays consistent and easy
    to override without touching code.

    Values are loaded from environment variables (via a local .env file,
    see .env.example) with a sensible default, so the app runs out of the
    box with no configuration required.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Delay (in seconds) the orchestrator waits between finishing one reviewer
# step and starting the next (orchestrator/pipeline.py). This is purely
# cosmetic pacing so the sequential fan-out/fan-in workflow is visibly
# watchable in the dashboard — it stands in for the real latency a live
# Cursor SDK call will eventually have, and can be tuned or set to 0
# without touching orchestration code.
REVIEW_STEP_DELAY_SECONDS = float(os.getenv("REVIEW_STEP_DELAY_SECONDS", "0.8"))

# --- Cursor SDK settings ----------------------------------------------------
#
# As of Sprint 7 the project targets Python 3.12 and reviewers/architecture.py
# imports cursor_sdk directly, in-process — there is no separate interpreter
# or subprocess bridge (that Sprint 5/6 design was removed once the whole app
# moved to 3.12; see DEVELOPMENT_CONTEXT.md).

# Cursor API key used to authenticate SDK calls. Read here (rather than each
# reviewer calling os.getenv directly) to keep every setting centralized in
# one place, per this file's own convention.
CURSOR_API_KEY = os.getenv("CURSOR_API_KEY")

# Model used for Cursor SDK-backed reviewers. Reuses the same env var
# REVIEWBOARD_MODEL already documented in .env.example rather than
# introducing a new one.
CURSOR_SDK_MODEL = os.getenv("REVIEWBOARD_MODEL", "composer-2.5")
