"""
ShipReady AI — Streamlit entrypoint.

Responsibility:
    This is the single entrypoint for the Streamlit application. Its job is
    strictly limited to configuring the page and invoking the dashboard —
    it must NOT contain reviewer logic, prompt construction, or Cursor SDK
    calls directly. All of that lives in reviewers/, orchestrator/, and
    ui/dashboard.py.

Current flow:
    1. Configure the Streamlit page (title, icon, layout).
    2. Render the dashboard (ui.dashboard.render_dashboard), which builds a
       SubmissionInput (models.review_models) from the uploaded files and
       hands it to the orchestration pipeline
       (orchestrator.pipeline.run_review_pipeline).

Planned (future sprint):
    Replace each reviewer's placeholder review() with a real Cursor SDK
    call — not wired up yet.
"""

import streamlit as st

from ui.dashboard import render_dashboard


def main() -> None:
    """Application entrypoint: configure the page and render the dashboard."""
    st.set_page_config(
        page_title="ShipReady AI",
        page_icon="🚀",
        layout="wide",
    )
    render_dashboard()


if __name__ == "__main__":
    main()
