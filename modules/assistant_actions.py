"""Assistant callbacks kept separate from the existing filter helpers."""

import streamlit as st


def open_assistant(question=None):
    """Open the assistant; optional questions are answered using the current scope."""
    st.session_state["workspace"] = "SupplyIQ assistant"
    if question:
        st.session_state["assistant_pending_question"] = question


def queue_question(question):
    st.session_state["assistant_pending_question"] = question
