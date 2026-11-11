"""Assistant callbacks kept separate from the existing filter helpers."""

import streamlit as st


def open_assistant(question=None):
    """Open the dashboard chat dialog without changing the active page."""
    st.session_state["assistant_dialog_open"] = True
    if question:
        st.session_state["assistant_pending_question"] = question


def queue_question(question):
    st.session_state["assistant_pending_question"] = question
