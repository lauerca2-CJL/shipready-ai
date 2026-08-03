"""
Reusable Streamlit UI components for the ShipReady AI dashboard.

Responsibility:
    Presentation-only building blocks used by ui/dashboard.py: the page
    header, the input widgets, the run button, and the review sections.

    Every function here only renders Streamlit widgets and returns raw UI
    values (uploaded file objects, a button-click boolean, a badge string).
    None of them construct a SubmissionInput, call the orchestration
    pipeline, or contain any reviewer/business logic — that wiring belongs
    to ui/dashboard.py.

Sprint 11 note: reviewer cards became `st.expander`s, and a couple of small
formatting helpers (`decision_badge()`, `_body_text()`) now read a
completed step's real `ReviewResult`/`ReleaseDecision` object (yielded by
orchestrator/pipeline.py as of this sprint) instead of a pre-rendered
string, so the expander title can show a decision badge. They use
`getattr(...)` duck-typing rather than importing `models.review_models` and
branching on `isinstance` — keeps this module decoupled from the model
layer for what's still just picking which of two already-known field names
to read, the same "presentation reads structured data, doesn't compute it"
principle `render_status_card` already applied when it branched on
`status == "Complete"`.
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

# Sprint 11: which reviewers' expanders start open. Architecture and CAB are
# the two reviewers with real, structured findings worth seeing immediately;
# Security/QA/Operations are still one-line placeholders, so collapsed by
# default keeps the initial view focused rather than showing three
# expanders with nothing substantial in them yet.
_DEFAULT_EXPANDED = {
    "Architecture": True,
    "Security": False,
    "QA": False,
    "Operations": False,
    "Change Advisory Board": True,
}

# For reviewers still on a hardcoded verdict (no `decision` field populated
# yet) — security.py/qa.py/operations.py as of this sprint. Duplicated from
# reviewers/cab.py's own small map rather than imported — ui/ doesn't
# depend on reviewers/ (ARCHITECTURE.md's layering rule).
_VERDICT_TO_LABEL = {"approve": "PASS", "approve_with_comments": "NEEDS_CHANGES", "block": "BLOCK"}
_LABEL_EMOJI = {"PASS": "✅", "APPROVE": "✅", "NEEDS_CHANGES": "🟠", "BLOCK": "🔴"}


def inject_compact_styles() -> None:
    """
    Minimal, presentation-only CSS — deliberately small, since Sprint 11
    prefers Streamlit-native spacing (headers, dividers, `st.container`)
    over custom CSS wherever that's enough on its own. This just gives
    expanders a bit of breathing room between them, which there's no clean
    native knob for.

    Purely cosmetic: targets only stable, generic selectors rather than
    internal Streamlit test-ids, so it degrades harmlessly if Streamlit's
    internal markup ever changes. No functional behavior depends on this.
    """
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            div[data-testid="stExpander"] {
                margin-bottom: 0.75rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """
    Render the application header: title, subtitle, tagline, and a
    one-line explanation of what the tool actually does — enterprise
    framing for an interview demo, per Sprint 11.
    """
    st.title("🚢 ShipReady AI")
    st.markdown("##### AI-Powered Change Advisory Board")
    st.caption("Enterprise Pull Request Review using Specialized AI Reviewers")
    st.markdown(
        "Specialized AI reviewers analyze a pull request in parallel, then a "
        "Change Advisory Board synthesizes their findings into a single release recommendation."
    )
    st.divider()


def render_input_section() -> Tuple[Optional[object], Optional[object]]:
    """
    Render the two submission inputs side by side, inside a bordered
    container with a short lead-in line — makes the upload step read as a
    deliberate, distinct stage of the workflow rather than two bare
    widgets floating on the page (Sprint 11).

    Returns the raw Streamlit UploadedFile objects (or None if nothing has
    been uploaded yet). This module stays presentation-only: reading their
    bytes and assembling a SubmissionInput is done by the caller
    (ui/dashboard.py), per the layering in ARCHITECTURE.md.
    """
    st.header("1. Submission")
    with st.container(border=True):
        st.caption("Upload the artifacts for the pull request under review.")
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
    st.write("")
    clicked = st.button("▶️ Run Review", type="primary", use_container_width=True)
    st.divider()
    return clicked


def decision_badge(result_obj: Optional[object]) -> Optional[str]:
    """
    Best-effort "<emoji> LABEL" badge for a completed step, read straight
    off the real `ReviewResult`/`ReleaseDecision` object the orchestrator
    yields (Sprint 11) — no parsing of rendered markdown text needed.
    Returns None if there's nothing to read yet (still Pending).

    `ReleaseDecision.cab_decision` (APPROVE/NEEDS_CHANGES/BLOCK) and
    `ReviewResult.decision` (PASS/NEEDS_CHANGES/BLOCK) are checked first;
    `ReviewResult.verdict` (always populated, even by the still-hardcoded
    security.py/qa.py/operations.py) is the fallback so every reviewer gets
    a badge, not just the two with real SDK integrations.
    """
    if result_obj is None:
        return None
    label = getattr(result_obj, "cab_decision", None) or getattr(result_obj, "decision", None)
    if label is None:
        label = _VERDICT_TO_LABEL.get(result_obj.verdict, result_obj.verdict.upper())
    emoji = _LABEL_EMOJI.get(label, "\u26aa")
    return f"{emoji} {label.replace('_', ' ')}"


def _body_text(result_obj: object) -> str:
    """
    The markdown to show inside a completed reviewer's expander —
    `ReleaseDecision.rationale` for CAB, `ReviewResult.summary` for the
    other four. Both are already-rendered report markdown as of Sprints
    8/9/10; this reads it unchanged (Sprint 11 doesn't touch how either is
    built, only where it's displayed).
    """
    return getattr(result_obj, "rationale", None) or result_obj.summary


def render_reviewer_section(
    icon: str,
    name: str,
    status: str,
    description: str,
    result_obj: Optional[object] = None,
    placeholder: Optional[object] = None,
) -> object:
    """
    Render (or re-render) a single reviewer as an `st.expander`.

    If `placeholder` (an `st.empty()` slot) is given, it's drawn into that
    slot, replacing whatever it held before — this is what lets the
    dashboard flip a section from "Pending" to "Complete" in place as the
    orchestrator finishes each step. Returns the placeholder used, so
    callers can keep it for a later update.

    The expander's title includes a decision badge once `result_obj` is
    available (see decision_badge()); its default open/closed state comes
    from _DEFAULT_EXPANDED, keyed by `name`. While Pending, the body is the
    short static blurb from STATUS_CARDS; once Complete, it's that
    reviewer's real report markdown, rendered as-is via st.markdown (see
    _body_text()) — same "Complete gets real markdown" rule
    render_status_card used pre-Sprint-11, just now backed by the object
    instead of its pre-rendered string.
    """
    target = placeholder if placeholder is not None else st.empty()
    badge = decision_badge(result_obj) if status == "Complete" else None
    title = f"{icon} {name}" + (f" — {badge}" if badge else f"  ({status})")

    with target.container():
        with st.expander(title, expanded=_DEFAULT_EXPANDED.get(name, False)):
            if status == "Complete":
                st.markdown(_body_text(result_obj))
            else:
                st.caption(description)
    return target


def render_review_board(results: Optional[dict] = None) -> dict:
    """
    Render one expander per reviewer, in fixed order, stacked vertically
    with visible spacing between them (Sprint 11 — replaces the old
    two-per-row bordered-card grid now that each reviewer's content is
    substantial enough to warrant its own full-width, expandable section).

    `results` maps a reviewer name (see STATUS_CARDS) to its completed
    `ReviewResult`/`ReleaseDecision`; any name missing from it is still
    Pending. Returns a dict mapping each reviewer name to the `st.empty()`
    placeholder its section was drawn into, so a caller (the orchestrator
    loop in ui/dashboard.py) can update individual sections later without
    re-rendering the whole board.
    """
    st.header("2. Review Status")
    results = results or {}
    placeholders = {}

    for card in STATUS_CARDS:
        result_obj = results.get(card["name"])
        status = "Complete" if result_obj is not None else "Pending"
        placeholders[card["name"]] = render_reviewer_section(
            card["icon"], card["name"], status, card["description"], result_obj
        )

    return placeholders
