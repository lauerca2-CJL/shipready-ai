"""
Streamlit presentation layer.

Responsibility:
    Contains ONLY rendering and input-collection logic. This package must
    never call the Cursor SDK directly or construct prompts — it talks to
    the orchestration layer (reviewboard.orchestration.pipeline) exclusively
    through plain data models (SubmissionInput, ReviewResult,
    ReleaseRecommendation). Keeping this boundary strict means the
    orchestration logic stays testable without spinning up Streamlit.

Modules:
    sidebar.py   Collects the git diff, PR description, and optional API
                 spec from the user.
    results.py   Renders ReviewResults and the final ReleaseRecommendation.
    state.py     Streamlit session_state helpers so reruns don't lose
                 in-progress uploads or completed review results.
"""
