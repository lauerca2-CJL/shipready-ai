"""
Streamlit dashboard.

Responsibility:
    Own all Streamlit rendering and input collection for ShipReady AI:
        - Collect a SubmissionInput from the user (git diff, PR description,
          optional API specification).
        - Trigger the orchestration pipeline (orchestrator/pipeline.py) on
          submission.
        - Render each reviewer's ReviewResult (verdict, summary, findings).
        - Render the CAB reviewer's final ReleaseDecision (decision,
          rationale, conditions).
        - Persist in-progress/completed pipeline state across Streamlit
          reruns.

    This module must NOT call the Cursor SDK directly or construct prompts —
    it only talks to orchestrator/pipeline.py and models/review_models.py.

Planned signature (not yet implemented):
    def render_dashboard() -> None: ...

Do NOT implement business logic in this increment. This module currently
only documents the dashboard's responsibility.
"""

# TODO: import streamlit as st
# TODO: from orchestrator.pipeline import run_review_pipeline
# TODO: from models.review_models import SubmissionInput
# TODO: implement render_dashboard(): input collection, pipeline trigger,
#       and results rendering.
