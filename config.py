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

# --- Cursor SDK bridge settings (Sprint 6) ---------------------------------
#
# cursor-sdk requires Python 3.10+; this app targets Python 3.9.6 and must
# never import cursor_sdk directly. reviewers/architecture.py instead shells
# out to sdk_bridge.py using a SEPARATE Python 3.10+ interpreter. See
# DEVELOPMENT_CONTEXT.md (Sprint 5/6) for the full setup story.

# Path to the Python 3.10+ interpreter that has cursor-sdk installed
# (requirements-sdk.txt). Defaults to the conventional local venv from
# Sprint 5; override via env var if that interpreter lives elsewhere.
CURSOR_SDK_PYTHON = os.getenv(
    "CURSOR_SDK_PYTHON",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv-sdk", "bin", "python"),
)

# Model passed to the Cursor SDK bridge. Reuses the same env var
# REVIEWBOARD_MODEL already documented in .env.example rather than
# introducing a new one.
CURSOR_SDK_MODEL = os.getenv("REVIEWBOARD_MODEL", "composer-2.5")

# Seconds to wait for the sdk_bridge.py subprocess before giving up.
CURSOR_SDK_BRIDGE_TIMEOUT_SECONDS = float(os.getenv("CURSOR_SDK_BRIDGE_TIMEOUT_SECONDS", "180"))
