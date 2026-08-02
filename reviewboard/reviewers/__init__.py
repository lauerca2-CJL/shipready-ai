"""
Specialized reviewer agents.

Each module in this package wraps exactly one Cursor SDK agent persona with
a single area of responsibility. None of these classes should know about
Streamlit, and none except the Release Manager should know about other
reviewers' outputs.

Modules:
    base.py                    Shared contract/base class for the four
                                diff-reviewers.
    architecture_reviewer.py   Structural/design soundness of the diff.
    security_reviewer.py       Security risk in the diff.
    qa_reviewer.py              Testability/test coverage implications.
    operations_reviewer.py     Deployability/operational risk.
    release_manager.py         Synthesizes all reviews into a final
                                recommendation. Does NOT read the diff.
"""
