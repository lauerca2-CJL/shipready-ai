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
