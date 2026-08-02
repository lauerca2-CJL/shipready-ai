"""
ShipReady AI — Streamlit entrypoint.

Responsibility:
    This is the single entrypoint for the Streamlit application. Its job is
    strictly limited to invoking the dashboard — it must NOT contain
    reviewer logic, prompt construction, or Cursor SDK calls directly. All
    of that lives in reviewers/, orchestrator/, and ui/dashboard.py.

Planned flow (not yet implemented):
    1. Render the dashboard (ui.dashboard.render_dashboard), which collects:
        - Git diff (paste or file upload)
        - Pull Request description
        - Optional API specification
    2. On submission, the dashboard builds a SubmissionInput
       (models.review_models).
    3. The dashboard hands the SubmissionInput to the orchestration pipeline
       (orchestrator.pipeline.run_review_pipeline).
    4. The dashboard renders the resulting ReleaseDecision and each
       reviewer's ReviewResult.

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: import streamlit as st
# TODO: from ui.dashboard import render_dashboard


def main() -> None:
    """Application entrypoint. Will configure the page and render the dashboard."""
    raise NotImplementedError("ShipReady AI UI is not implemented yet.")


if __name__ == "__main__":
    main()
