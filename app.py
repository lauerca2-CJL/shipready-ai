"""
ReviewBoard AI — Streamlit entrypoint.

Responsibility:
    This is the single entrypoint for the Streamlit application. Its job is
    strictly limited to wiring together UI components and the orchestration
    pipeline — it must NOT contain reviewer logic, prompt construction, or
    Cursor SDK calls directly. All of that lives in reviewboard.reviewers
    and reviewboard.orchestration.

Planned flow (not yet implemented):
    1. Render the sidebar (reviewboard.ui.sidebar) to collect:
        - Git diff (paste or file upload)
        - Pull Request description
        - Optional API specification
    2. On submission, build a SubmissionInput (reviewboard.models.inputs).
    3. Hand the SubmissionInput to the orchestration pipeline
       (reviewboard.orchestration.pipeline.run_review_pipeline).
    4. Render the resulting ReleaseRecommendation and each reviewer's
       ReviewResult via reviewboard.ui.results.
    5. Persist relevant state via reviewboard.ui.state so Streamlit reruns
       don't lose in-progress or completed review data.

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: import streamlit as st
# TODO: from reviewboard.ui import sidebar, results, state
# TODO: from reviewboard.orchestration.pipeline import run_review_pipeline


def main() -> None:
    """Application entrypoint. Will configure the page and render the UI."""
    raise NotImplementedError("ReviewBoard AI UI is not implemented yet.")


if __name__ == "__main__":
    main()
