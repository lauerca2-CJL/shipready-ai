"""
Streamlit dashboard.

Responsibility:
    Assemble the reusable components in ui/components.py into the
    ShipReady AI dashboard layout: header, submission inputs, the run
    action, and the review status board. It also builds the
    SubmissionInput (models.review_models) that gets handed to the
    orchestrator, since ARCHITECTURE.md assigns that responsibility to
    this module.

    This module renders UI and drives the orchestrator's generator, but it
    does not itself construct prompts, call the Cursor SDK, or contain any
    reviewer logic — that all lives in reviewers/.

Sprint 4 note: clicking "Run Review" now builds a real SubmissionInput from
the uploaded diff/PR files (reading their raw bytes as text) and passes it
into orchestrator.pipeline.run_review_pipeline(), which runs the four
diff-reviewers and the CAB reviewer in order and yields after each one so
this module can flip that reviewer's status card from "Pending" to
"Complete" in place. Every reviewer's review() body is still a hardcoded
placeholder — no Cursor SDK or LLM call happens anywhere in this flow yet;
the pipeline now simply has real input to (eventually) act on.

Planned (future sprint):
    - Replace each reviewer's placeholder review() with a real Cursor SDK
      call.
"""

from typing import Optional

import streamlit as st

from models.review_models import SubmissionInput
from orchestrator.pipeline import run_review_pipeline
from ui.components import (
    STATUS_CARDS,
    inject_compact_styles,
    render_header,
    render_input_section,
    render_run_button,
    render_status_board,
    render_status_card,
)

_PENDING_STATUSES = {card["name"]: "Pending" for card in STATUS_CARDS}


def _read_uploaded_text(uploaded_file: Optional[object]) -> str:
    """
    Decode a Streamlit UploadedFile's raw bytes into text.

    Returns "" if no file was uploaded. Uses errors="replace" rather than
    raising on non-UTF-8 bytes — a malformed encoding shouldn't crash the
    dashboard; the placeholder reviewers don't inspect this text yet
    anyway, and a real reviewer implementation (future sprint) can decide
    how strict to be.
    """
    if uploaded_file is None:
        return ""
    return uploaded_file.getvalue().decode("utf-8", errors="replace")


def _build_submission(diff_file: Optional[object], pr_file: Optional[object]) -> SubmissionInput:
    """Turn the raw uploaded files from render_input_section() into a real SubmissionInput."""
    return SubmissionInput(
        diff_text=_read_uploaded_text(diff_file),
        pr_description=_read_uploaded_text(pr_file),
    )


def render_dashboard() -> None:
    """Render the full ShipReady AI dashboard."""
    inject_compact_styles()
    render_header()

    diff_file, pr_file = render_input_section()
    run_clicked = render_run_button()

    if "review_statuses" not in st.session_state:
        st.session_state.review_statuses = dict(_PENDING_STATUSES)

    if run_clicked:
        # Reset to Pending before drawing the board below, so re-running
        # the pipeline visibly restarts the animation instead of appearing
        # to skip straight to "Complete" for cards left over from a
        # previous run.
        st.session_state.review_statuses = dict(_PENDING_STATUSES)

    # Render the board exactly once per script run. Its placeholders are
    # then updated in place by the loop below, rather than re-rendering a
    # second board — that would stack a duplicate grid on the page.
    placeholders = render_status_board(st.session_state.review_statuses)

    if run_clicked:
        submission = _build_submission(diff_file, pr_file)
        card_by_name = {card["name"]: card for card in STATUS_CARDS}
        final_summary = ""

        for name, summary in run_review_pipeline(submission):
            st.session_state.review_statuses[name] = "Complete"
            card = card_by_name[name]
            render_status_card(
                card["icon"],
                card["name"],
                "Complete",
                summary,
                placeholder=placeholders[name],
            )
            final_summary = summary

        st.success(f"Review complete — CAB decision: {final_summary}")
