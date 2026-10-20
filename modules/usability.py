"""Small, explicit callbacks shared by navigation and filter controls."""

import streamlit as st
from .data_loader import DIMENSIONS, MONTHS


def reset_filters():
    st.session_state["filter_months"] = MONTHS.tolist()
    for column in DIMENSIONS:
        st.session_state["filter_" + column] = []


def set_period(start):
    st.session_state["filter_months"] = MONTHS[start:].tolist()


def navigate(page):
    st.session_state["workspace"] = page


def set_scenario(value):
    st.session_state["scenario_pct"] = value
