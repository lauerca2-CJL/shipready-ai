"""
Standalone Cursor SDK connectivity check.

Responsibility:
    Prove, independently of the rest of the app, that this project can
    configure the Cursor SDK and successfully complete one trivial
    round-trip request — a quick way to sanity-check credentials/network
    without going through the Streamlit dashboard. This is the ONLY thing
    this script does.

    This script is deliberately NOT imported by reviewers/, orchestrator/,
    ui/, or app.py, and does not share config.py. It is a standalone
    smoke test you run by hand from the command line.

    As of Sprint 7 the whole project targets Python 3.12 (see
    .python-version / requirements.txt), so this script runs in the same
    venv as the rest of the app — no separate interpreter needed (that was
    a Sprint 5/6 requirement before the project migrated off Python 3.9).

Usage:
    export CURSOR_API_KEY="cursor_..."   # or put it in .env (see .env.example)
    python verify_cursor_sdk.py

Exit codes (mirrors the SDK's own failure-mode distinction):
    0 - the agent run finished successfully.
    1 - startup failure (CursorAgentError): auth, config, or network problem;
        the run never executed.
    2 - the run executed but the SDK reported result.status == "error".
"""

import os
import sys

from cursor_sdk import Agent, AgentOptions, CursorAgentError, LocalAgentOptions
from dotenv import load_dotenv

load_dotenv()

PROMPT = "Say hello in exactly one short sentence."
MODEL = os.getenv("REVIEWBOARD_MODEL", "composer-2.5")


def main() -> int:
    api_key = os.getenv("CURSOR_API_KEY")
    if not api_key:
        print(
            "CURSOR_API_KEY is not set. Copy .env.example to .env and fill it "
            "in, or export CURSOR_API_KEY directly.",
            file=sys.stderr,
        )
        return 1

    print(f"Sending a trivial prompt to the Cursor SDK (model={MODEL})...")

    try:
        result = Agent.prompt(
            PROMPT,
            AgentOptions(
                api_key=api_key,
                model=MODEL,
                local=LocalAgentOptions(cwd=os.getcwd()),
            ),
        )
    except CursorAgentError as err:
        # The run never executed: auth, config, or network problem.
        print(
            f"Startup failed (CursorAgentError): {err}\nretryable={getattr(err, 'is_retryable', 'unknown')}",
            file=sys.stderr,
        )
        return 1

    if result.status == "error":
        # The run executed but failed mid-flight.
        print(f"Run failed: status={result.status} id={getattr(result, 'id', 'unknown')}", file=sys.stderr)
        return 2

    print(f"Run finished: status={result.status}")
    print(f"Response:\n{result.result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
