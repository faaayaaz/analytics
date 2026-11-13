"""A focused conversation interface shared by the assistant page and dashboard dialog."""

import hashlib
import os
import re
import streamlit as st
from .ai_assistant import answer
from .assistant_actions import queue_question
from .presentation import display_table
from .visualizations import show, line, bar

STARTERS = [
    ("Summarize my data", "Summarize the main supply planning insights."),
    ("Top 10 SKUs", "Which 10 SKUs generated the highest sales in 2024?"),
    ("Demand variability", "Which products have the biggest demand swings?"),
    ("Show AZ products", "Which products belong to the AZ category?"),
    ("Declining categories", "Which categories experienced declining demand?"),
    ("Unusual changes", "Identify significant demand anomalies."),
]


def clear_conversation():
    st.session_state.messages = []
    st.session_state.chat_context = None
    st.session_state.pop("assistant_pending_question", None)


def api_configuration():
    key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        key = key or st.secrets.get("OPENAI_API_KEY", "")
        model = st.secrets.get("OPENAI_MODEL", model)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        pass
    return key, model


def conversation_markdown(messages):
    """Export only user-facing retained content, never configuration or provider metadata."""

    def safe(value):
        text = re.sub(
            r"""(?im)\b(OPENAI_API_KEY|API_KEY|PASSWORD|TOKEN)\s*[:=]\s*(?:"[^"]*"|'[^']*'|[^\s]+)""",
            r"\1=[redacted]",
            str(value),
        )
        return re.sub(r"\bsk-[A-Za-z0-9_-]{16,}", "[redacted key]", text)

    lines = [
        "# SupplyIQ conversation",
        "",
        "Retained messages for the current dashboard filter selection. Sales-based analysis; stock and supplier information are not provided.",
        "",
    ]
    for message in messages:
        if message.get("role") not in ["user", "assistant"]:
            continue
        lines.extend(
            [
                "## " + ("You" if message["role"] == "user" else "SupplyIQ"),
                "",
                safe(message.get("text", "")),
                "",
            ]
        )
        if message.get("scope_note"):
            lines.extend(["Question focus: " + safe(message["scope_note"]), ""])
        table = message.get("table")
        if table is not None and not table.empty:
            lines.extend(
                [
                    "Calculated results (CSV):",
                    "```csv",
                    safe(table.to_csv(index=False).rstrip()),
                    "```",
                    "",
                ]
            )
    return "\n".join(lines)


def render_assistant(data, months, thresholds, scope, compact=False):
    prefix = "supplyiq_dialog" if compact else "supplyiq_page"
    fingerprint = hashlib.sha256((scope + str(thresholds)).encode()).hexdigest()
    if st.session_state.get("chat_scope") != fingerprint:
        st.session_state.chat_scope = fingerprint
        pending_question = st.session_state.pop("assistant_pending_question", None)
        clear_conversation()
        if pending_question:
            st.session_state.assistant_pending_question = pending_question
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("chat_context", None)
    key, model = api_configuration()
    with st.container(key=prefix + "_toolbar"):
        scope_label, new, settings = st.columns([4, 1, 1], vertical_alignment="center")
        scope_label.caption(
            f"{data['product'].nunique():,} SKUs · {len(months)} selected months · Your dashboard filters stay applied"
        )
        new.button(
            "New chat",
            key=prefix + "_new",
            on_click=clear_conversation,
            width="stretch",
        )
        settings_panel = settings.popover("Settings", width="stretch")
        with settings_panel:
            st.caption("No API key is needed for built-in analysis.")
            enabled = st.toggle(
                "Use optional AI service",
                value=bool(key)
                and st.session_state.get("assistant_llm_enabled", False),
                key=prefix + "_ai",
                disabled=not bool(key),
            )
            st.session_state.assistant_llm_enabled = enabled
            if enabled:
                st.caption(
                    "The service receives your question, short conversation context and up to 15 aggregate result rows. Raw transaction data is not sent."
                )
            st.caption(
                "Answers use your selected sales data. Stock, supplier times and purchase requirements are not available. Changing data filters starts a fresh conversation."
            )
    conversation = st.container(
        height=340 if compact else 500,
        border=True,
        key=prefix + "_conversation",
        autoscroll=bool(st.session_state.messages),
    )
    question = st.chat_input(
        "Ask a question about your selected data…",
        key=prefix + "_input",
        max_chars=2000,
        disabled=data.empty,
    )
    queued = st.session_state.pop("assistant_pending_question", None)
    question = question or queued
    if question and not data.empty:
        with st.spinner("Checking your data…"):
            result = answer(
                question,
                data,
                months,
                thresholds,
                st.session_state.get("chat_context"),
                key if enabled else None,
                model,
            )
        st.session_state.messages.extend(
            [{"role": "user", "text": question}, {"role": "assistant", **result}]
        )
        st.session_state.messages = st.session_state.messages[-20:]
        st.session_state.chat_context = result["context"]
    with settings_panel:
        st.download_button(
            "Download conversation",
            conversation_markdown(st.session_state.messages).encode("utf-8"),
            file_name="supplyiq_conversation.md",
            mime="text/markdown",
            key=prefix + "_transcript",
            disabled=not st.session_state.messages,
            width="stretch",
        )
        st.caption(
            "Exports the retained conversation and calculated results for the current filters. New chat clears it."
        )
    with conversation:
        if data.empty:
            st.info("Select data in the dashboard before asking a question.")
        elif not st.session_state.messages:
            st.markdown(
                '<div class="assistant-welcome"><span class="assistant-emblem">✦</span><h2>What would you like to explore?</h2><p>Choose a question below or type your own. I’ll calculate the answer from your selected data.</p></div>',
                unsafe_allow_html=True,
            )
            for offset in (0, 2, 4):
                columns = st.columns(2)
                for column, (label, prompt) in zip(
                    columns, STARTERS[offset : offset + 2]
                ):
                    column.button(
                        label,
                        key=prefix + "_starter_" + label,
                        on_click=queue_question,
                        args=(prompt,),
                        help=prompt,
                        width="stretch",
                    )
        else:
            for i, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    st.write(message["text"])
                    if message["role"] == "assistant":
                        if (
                            message.get("scope_note")
                            and message["scope_note"] != "Dashboard selection"
                        ):
                            st.caption("Question focus: " + message["scope_note"])
                        notice = message.get("notice", "")
                        st.caption(
                            "AI service unavailable; using built-in analysis."
                            if "API unavailable" in notice
                            else "AI-assisted explanation"
                            if "LLM" in notice
                            else "Calculated from your selected data"
                        )
                        table = message.get("table")
                        if table is not None:
                            with st.expander(f"View {len(table):,} results & download"):
                                display_table(table, hide_index=True, width="stretch")
                                st.download_button(
                                    "Download result",
                                    table.to_csv(index=False).encode("utf-8-sig"),
                                    file_name="supplyiq_result.csv",
                                    mime="text/csv",
                                    key=prefix + f"_csv_{i}",
                                )
                            chart = message.get("chart")
                            if chart and not table.empty:
                                with st.expander("View chart"):
                                    kind, x, y = chart
                                    fig = (
                                        line(
                                            table,
                                            x,
                                            y,
                                            "Results from your data",
                                            (
                                                next(
                                                    column
                                                    for column in [
                                                        "product",
                                                        "brand",
                                                        "category",
                                                        "division",
                                                    ]
                                                    if column in table.columns
                                                )
                                            )
                                            if kind == "comparison"
                                            else None,
                                        )
                                        if kind in ["line", "comparison"]
                                        else bar(table, x, y, "Results from your data")
                                    )
                                    show(fig, key=prefix + f"_chart_{i}")
            st.caption("Continue with a question or choose another analysis:")
            followups = st.columns(3)
            for column, (label, prompt) in zip(
                followups,
                [
                    ("Top 10 SKUs", STARTERS[1][1]),
                    ("Monthly demand", "Show monthly demand growth"),
                    ("More questions", ""),
                ],
            ):
                if prompt:
                    column.button(
                        label,
                        key=prefix + "_follow_" + label,
                        on_click=queue_question,
                        args=(prompt,),
                        width="stretch",
                    )
                else:
                    with column.popover("More questions", width="stretch"):
                        for label, prompt in STARTERS:
                            st.button(
                                label,
                                key=prefix + "_more_" + label,
                                on_click=queue_question,
                                args=(prompt,),
                                width="stretch",
                            )
                        st.button(
                            "Explain missing stock data",
                            key=prefix + "_missing",
                            on_click=queue_question,
                            args=("What inventory should we replenish?",),
                            width="stretch",
                        )
    st.caption(
        "Sales-based planning support · Check results before making business decisions."
    )
