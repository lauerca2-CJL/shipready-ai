"""
Reusable Streamlit UI components for the ShipReady AI dashboard.

Responsibility:
    Presentation-only building blocks used by ui/dashboard.py: the page
    header, the input widgets, the run button, and the review status cards.

    Every function here only renders Streamlit widgets and returns raw UI
    values (uploaded file objects, a button-click boolean). None of them
    construct a SubmissionInput, call the orchestration pipeline, or
    contain any reviewer/business logic — that wiring belongs to a later
    sprint.
"""

from typing import Optional, Tuple

import streamlit as st

# Static description of the review board, driven by data rather than
# hardcoded per-card markup, so adding a sixth reviewer later is a one-line
# change here (see ARCHITECTURE.md, "Extensibility: adding a sixth reviewer").
STATUS_CARDS = [
    {
        "icon": "🏗️",
        "name": "Architecture",
        "description": "Evaluates structural design, module boundaries, and long-term maintainability.",
    },
    {
        "icon": "🔒",
        "name": "Security",
        "description": "Scans for vulnerabilities, unsafe dependencies, and authN/authZ risks.",
    },
    {
        "icon": "🧪",
        "name": "QA",
        "description": "Assesses test coverage and verifies edge cases are handled.",
    },
    {
        "icon": "⚙️",
        "name": "Operations",
        "description": "Reviews deployability, rollback safety, and observability.",
    },
    {
        "icon": "🏛️",
        "name": "Change Advisory Board",
        "description": "Synthesizes all reviewer findings into a final release decision.",
    },
]


def inject_compact_styles() -> None:
    """
    Apply minimal, presentation-only CSS to tighten Streamlit's fairly
    generous default vertical spacing for a denser, more professional
    dashboard feel.

    Purely cosmetic: targets only stable, generic selectors (the top-level
    `.block-container` wrapper and plain `h3` tags) rather than internal
    Streamlit test-ids, so it degrades harmlessly if Streamlit's internal
    markup ever changes. No functional behavior depends on this.
    """
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 2rem;
                padding-bottom: 1.5rem;
            }
            h3 {
                margin-top: 0.25rem;
                margin-bottom: 0.5rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Render a compact dashboard title and subtitle."""
    st.subheader("🚀 ShipReady AI")
    st.caption("AI-powered Change Advisory Board")


def render_input_section() -> Tuple[Optional[object], Optional[object]]:
    """
    Render the two submission inputs side by side.

    Returns the raw Streamlit UploadedFile objects (or None if nothing has
    been uploaded yet). This module stays presentation-only: reading their
    bytes and assembling a SubmissionInput is done by the caller
    (ui/dashboard.py), per the layering in ARCHITECTURE.md.
    """
    st.subheader("Submission")
    col_diff, col_pr = st.columns(2, gap="medium")

    with col_diff:
        diff_file = st.file_uploader(
            "Git Diff",
            type=["diff", "patch", "txt"],
            help="Upload the unified git diff for the change under review.",
        )

    with col_pr:
        pr_file = st.file_uploader(
            "Pull Request Description",
            type=["md", "txt"],
            help="Upload the PR title/description as a text or markdown file.",
        )

    return diff_file, pr_file


def render_run_button() -> bool:
    """Render the primary call-to-action. Returns True if clicked this run."""
    return st.button("▶️ Run Review", type="primary", use_container_width=True)


_STATUS_COLORS = {
    "Pending": "orange",
    "Complete": "green",
}


def render_status_card(
    icon: str,
    name: str,
    status: str,
    description: str,
    placeholder: Optional[object] = None,
) -> object:
    """
    Render (or re-render) a single, compact bordered status card.

    If `placeholder` (an `st.empty()` slot) is given, the card is drawn
    into it, replacing whatever it held before — this is what lets the
    dashboard flip a card from "Pending" to "Complete" in place as the
    orchestrator finishes each step. Returns the placeholder used, so
    callers can keep it for a later update.

    While Pending, `description` is the short static blurb from
    STATUS_CARDS, rendered as a caption. Once Complete, `description` is a
    reviewer's real `ReviewResult.summary` — for reviewers/architecture.py
    (Sprint 8) that's a full markdown report (headings + bullets), so it's
    rendered with st.markdown instead of st.caption. Plain one-line
    placeholder summaries (security.py, qa.py, operations.py, cab.py) still
    render fine as plain markdown text — this is a display-only change,
    no reviewer/orchestrator behavior depends on it.
    """
    target = placeholder if placeholder is not None else st.empty()
    color = _STATUS_COLORS.get(status, "orange")
    with target.container(border=True):
        st.markdown(f"**{icon} {name}** · :{color}[{status}]")
        if status == "Complete":
            st.markdown(description)
        else:
            st.caption(description)
    return target


def render_status_board(statuses: Optional[dict] = None) -> dict:
    """
    Render one status card per reviewer in a responsive grid.

    Layout: the four diff-reviewers (Architecture, Security, QA, Operations)
    are arranged two-per-row; the CAB card — the single fan-in synthesis
    point for the other four — spans the full width on its own row below
    them. On narrow viewports, Streamlit's columns stack vertically on
    their own, so this remains readable on mobile without extra CSS.

    `statuses` maps a reviewer name (see STATUS_CARDS) to its current
    status string ("Pending" or "Complete"); any name missing from it
    defaults to "Pending". Returns a dict mapping each reviewer name to the
    `st.empty()` placeholder its card was drawn into, so a caller (e.g. the
    orchestrator loop in ui/dashboard.py) can update individual cards later
    without re-rendering the whole board.
    """
    st.subheader("Review Status")
    statuses = statuses or {}

    diff_reviewer_cards, cab_card = STATUS_CARDS[:-1], STATUS_CARDS[-1]
    placeholders = {}

    for row_start in range(0, len(diff_reviewer_cards), 2):
        row_cards = diff_reviewer_cards[row_start : row_start + 2]
        columns = st.columns(2, gap="medium")
        for column, card in zip(columns, row_cards):
            with column:
                status = statuses.get(card["name"], "Pending")
                placeholders[card["name"]] = render_status_card(
                    card["icon"], card["name"], status, card["description"]
                )

    status = statuses.get(cab_card["name"], "Pending")
    placeholders[cab_card["name"]] = render_status_card(
        cab_card["icon"], cab_card["name"], status, cab_card["description"]
    )

    return placeholders
