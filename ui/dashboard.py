"""
Streamlit dashboard.

Responsibility:
    Assemble the reusable components in ui/components.py into the
    ShipReady AI dashboard layout: header, submission inputs, the run
    action, and the review status board.

    This module (and ui/components.py) render UI only. They do not call
    the Cursor SDK, construct prompts, build a SubmissionInput, or invoke
    the orchestration pipeline (orchestrator/pipeline.py) — that wiring is
    deferred to a later sprint. Today, clicking "Run Review" only shows a
    placeholder acknowledgement.

Planned (future sprint):
    - Build a SubmissionInput (models.review_models) from the uploaded
      files once render_run_button() returns True.
    - Hand it to orchestrator.pipeline.run_review_pipeline().
    - Replace each status card's hardcoded "Pending" state with the real
      ReviewResult verdict, and the CAB card with the ReleaseDecision.
    - Persist in-progress/completed pipeline state across Streamlit reruns.
"""

import streamlit as st

from ui.components import (
    inject_compact_styles,
    render_header,
    render_input_section,
    render_run_button,
    render_status_board,
)


def render_dashboard() -> None:
    """Render the full ShipReady AI dashboard."""
    inject_compact_styles()
    render_header()

    render_input_section()
    run_clicked = render_run_button()
    if run_clicked:
        # TODO: replace with a real orchestrator.pipeline.run_review_pipeline() call.
        st.info("Review pipeline is not implemented yet — coming in a future sprint.")

    render_status_board()
