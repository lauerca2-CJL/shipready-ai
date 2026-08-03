"""
Cursor SDK bridge — the ONLY file in this repo allowed to `import cursor_sdk`.

Responsibility:
    A tiny, generic request/response process: read one JSON request from
    stdin, make one `Agent.prompt(...)` call, write one JSON response to
    stdout, exit. Nothing else. It knows nothing about reviewers,
    ReviewResult, or any other app concept — that keeps it reusable if a
    future sprint wires up a second SDK-backed reviewer, and keeps this
    file runnable as its own tiny contract independent of the app.

Why this file exists (see DEVELOPMENT_CONTEXT.md, Sprint 5/6):
    cursor-sdk requires Python 3.10+; the rest of this app targets Python
    3.9.6 and must not import cursor_sdk directly. reviewers/architecture.py
    (Python 3.9) invokes THIS script as a subprocess using a separate
    Python 3.10+ interpreter (config.CURSOR_SDK_PYTHON), communicating over
    stdin/stdout JSON only. No shared imports, no shared process.

Request (stdin, one JSON object):
    {"prompt": "<the full prompt text>", "model": "composer-2.5"}

Response (stdout, one JSON object, always exactly one line):
    {"status": "success" | "startup_error" | "run_error",
     "text": "<agent's response text>" | null,
     "error": null | "<human-readable error message>"}

Exit codes (mirror the SDK's own failure-mode distinction, same convention
as verify_cursor_sdk.py):
    0 - status == "success"
    1 - status == "startup_error" (CursorAgentError; run never executed —
        auth, config, network)
    2 - status == "run_error" (the run executed but the SDK reported
        result.status == "error")
"""

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

try:
    from cursor_sdk import Agent, AgentOptions, CursorAgentError, LocalAgentOptions
except ImportError:
    print(
        json.dumps(
            {
                "status": "startup_error",
                "text": None,
                "error": (
                    "cursor-sdk is not installed in this interpreter. "
                    "Requires Python 3.10+: pip install -r requirements-sdk.txt"
                ),
            }
        )
    )
    sys.exit(1)


def main() -> int:
    try:
        request = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        print(json.dumps({"status": "startup_error", "text": None, "error": f"Invalid JSON request: {exc}"}))
        return 1

    prompt = request.get("prompt", "")
    model = request.get("model") or "composer-2.5"

    api_key = os.getenv("CURSOR_API_KEY")
    if not api_key:
        print(
            json.dumps(
                {
                    "status": "startup_error",
                    "text": None,
                    "error": "CURSOR_API_KEY is not set in the bridge's environment.",
                }
            )
        )
        return 1

    try:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model=model,
                local=LocalAgentOptions(cwd=os.getcwd()),
            ),
        )
    except CursorAgentError as err:
        print(json.dumps({"status": "startup_error", "text": None, "error": str(err)}))
        return 1

    if result.status == "error":
        print(json.dumps({"status": "run_error", "text": None, "error": f"run id={getattr(result, 'id', 'unknown')}"}))
        return 2

    print(json.dumps({"status": "success", "text": result.result, "error": None}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
