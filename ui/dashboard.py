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
this module can flip that reviewer's section from "Pending" to "Complete"
in place.

Sprint 11 note: the orchestrator now yields each step's real
`ReviewResult`/`ReleaseDecision` object (was a pre-rendered summary
string) — this module keeps those objects in session state (keyed by
reviewer name) instead of a plain status string, so ui/components.py's
expander titles can show a decision badge. No reviewer/orchestrator logic
changed; this is purely which data this module hangs on to for display.
"""

from typing import Optional

import streamlit as st

from models.review_models import SubmissionInput
from orchestrator.pipeline import run_review_pipeline
from ui.components import (
    STATUS_CARDS,
    decision_badge,
    inject_compact_styles,
    render_header,
    render_input_section,
    render_review_board,
    render_reviewer_section,
    render_run_button,
)


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

    if "review_results" not in st.session_state:
        st.session_state.review_results = {}

    if run_clicked:
        # Reset to Pending before drawing the board below, so re-running
        # the pipeline visibly restarts the animation instead of appearing
        # to skip straight to "Complete" for sections left over from a
        # previous run.
        st.session_state.review_results = {}

    # Render the board exactly once per script run. Its placeholders are
    # then updated in place by the loop below, rather than re-rendering a
    # second board — that would stack a duplicate set of sections on the page.
    placeholders = render_review_board(st.session_state.review_results)

    if run_clicked:
        submission = _build_submission(diff_file, pr_file)
        card_by_name = {card["name"]: card for card in STATUS_CARDS}
        final_result = None

        for name, result_obj in run_review_pipeline(submission):
            st.session_state.review_results[name] = result_obj
            card = card_by_name[name]
            render_reviewer_section(
                card["icon"],
                card["name"],
                "Complete",
                card["description"],
                result_obj,
                placeholder=placeholders[name],
            )
            final_result = result_obj

        badge = decision_badge(final_result) or "n/a"
        st.success(f"Review complete — CAB decision: {badge}")
