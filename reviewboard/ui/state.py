"""
Streamlit session state helpers.

Responsibility:
    Centralize all st.session_state key names and access patterns so the
    rest of the UI package doesn't scatter raw string keys throughout.
    Tracks things like: the last SubmissionInput, in-flight pipeline status,
    and the last PipelineResult, so a Streamlit rerun doesn't lose completed
    or in-progress work.

Planned contents (not yet implemented):
    - Typed accessor functions, e.g. get_last_result(), set_last_result(...).

Left intentionally unimplemented for this scaffolding increment.
"""

# TODO: implement session state accessors.
