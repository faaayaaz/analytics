import hashlib
import pandas as pd
import streamlit as st
from modules.data_loader import (
    load_workbook,
    filter_data,
    DEFAULT_PATH,
    DIMENSIONS,
    MONTHS,
)
from modules import views
from modules.usability import reset_filters, set_period, navigate
from modules.assistant_actions import open_assistant
from modules.theme import apply_theme
from modules.assistant_ui import render_assistant

st.set_page_config(
    page_title="Consumer Supply Planning Intelligence", page_icon="◈", layout="wide"
)
apply_theme()


def dismiss_supplyiq_dialog():
    st.session_state["assistant_dialog_open"] = False


def use_available_months(months):
    st.session_state["filter_months"] = months


@st.dialog(
    "SupplyIQ — AI Planning Assistant",
    width="large",
    on_dismiss=dismiss_supplyiq_dialog,
)
def supplyiq_chat_dialog():
    render_assistant(filtered, selected_months, thresholds, scope, compact=True)


@st.cache_data(show_spinner="Reading and validating the workbook…", max_entries=3)
def cached_load(payload):
    return load_workbook(payload)


with st.sidebar:
    st.title("◈ SupplyIQ")
    st.caption("DEMAND • INSIGHT • ACTION")
    page = st.radio(
        "Pages",
        [
            "Executive overview",
            "SKU analysis",
            "Demand forecasting",
            "SupplyIQ assistant",
            "Data quality & downloads",
        ],
        key="workspace",
    )
    st.divider()
    with st.expander("Data source"):
        uploaded = st.file_uploader("Replace assessment workbook", type=["xlsx"])
        st.caption(
            "The supplied assessment workbook is used unless you upload a replacement."
        )
try:
    payload = uploaded.getvalue() if uploaded else DEFAULT_PATH.read_bytes()
    data, report = cached_load(payload)
except (ValueError, KeyError, OSError, TypeError) as exc:
    st.error(f"Workbook could not be loaded: {exc}")
    st.stop()

heading, assistant_button, summary_button = st.columns(
    [4.5, 1.1, 1.5], vertical_alignment="center"
)
with heading:
    title = (
        "SupplyIQ — AI Planning Assistant"
        if page == "SupplyIQ assistant"
        else "Consumer Supply Planning Intelligence"
    )
    st.markdown(
        '<div class="dashboard-heading"><div class="eyebrow"><span class="brand-mark">↗</span> SUPPLYIQ / PLANNING INTELLIGENCE</div><h1>'
        + title
        + "</h1></div>",
        unsafe_allow_html=True,
    )
if page != "SupplyIQ assistant":
    assistant_button.button(
        "Ask SupplyIQ",
        icon=":material/chat:",
        key="open_supplyiq",
        on_click=open_assistant,
        type="primary",
        width="stretch",
    )
    summary_button.button(
        "Summarize my selection",
        icon=":material/insights:",
        key="summary_supplyiq",
        on_click=open_assistant,
        args=("Summarize the main supply planning insights.",),
        width="stretch",
    )

filter_panel = (
    st.expander("Change dashboard filters", expanded=False)
    if page == "SupplyIQ assistant"
    else st.container(border=True, key="global_filter_bar")
)
with filter_panel:
    st.session_state.setdefault("filter_months", MONTHS.tolist())
    division_slot, category_slot, brand_slot, period_slot = st.columns(
        [1, 1, 1, 0.8], vertical_alignment="bottom"
    )
    common_slots = {
        "division": division_slot,
        "category": category_slot,
        "brand": brand_slot,
    }
    with (
        period_slot,
        st.popover("Period & reset", icon=":material/calendar_month:", width="stretch"),
    ):
        full, last = st.columns(2)
        full.button("Full year", on_click=set_period, args=(0,), width="stretch")
        last.button("Q4 only", on_click=set_period, args=(9,), width="stretch")
        st.button("Last 6 months", on_click=set_period, args=(6,), width="stretch")
        selected_months = st.multiselect(
            "Month",
            MONTHS.tolist(),
            key="filter_months",
            format_func=lambda month: month.strftime("%b %Y"),
        )
        st.button(
            "Reset all filters",
            key="sidebar_reset",
            on_click=reset_filters,
            width="stretch",
        )
        st.caption(
            "An empty month selection means no records. Empty product or customer filters mean all available values."
        )
    advanced = st.sidebar.expander("More filters", expanded=False)
    selections = {}
    available = data
    for column in DIMENSIONS:
        options = sorted(available[column].unique())
        state_key = "filter_" + column
        if state_key in st.session_state:
            st.session_state[state_key] = [
                value for value in st.session_state[state_key] if value in options
            ]
        with common_slots.get(column, advanced):
            values = st.multiselect(
                column.replace("_", " ").title(),
                options,
                placeholder="All",
                key=state_key,
                help="Type to search. Leave empty for all. Filters apply across the dashboard and SupplyIQ.",
            )
        selections[column] = values if values else options
        if values:
            available = available.loc[available[column].isin(values)]

with st.sidebar:
    with st.expander("ABC–XYZ settings"):
        a = st.number_input(
            "A cumulative revenue %",
            min_value=1.0,
            max_value=98.0,
            value=80.0,
            step=1.0,
        )
        b = st.number_input(
            "B cumulative revenue %",
            min_value=2.0,
            max_value=99.0,
            value=95.0,
            step=1.0,
        )
        x = st.number_input(
            "X maximum CV", min_value=0.0, max_value=5.0, value=0.5, step=0.1
        )
        y = st.number_input(
            "Y maximum CV", min_value=0.1, max_value=10.0, value=1.0, step=0.1
        )
    with st.expander("Help & data limits"):
        st.write(
            "SKU means product code. Net demand means units sold minus returns. ABC groups products by sales value; XYZ groups them by demand consistency. CV measures changes compared with average demand. N/A means a result cannot be calculated."
        )
        st.write(
            "This is adjusted, anonymized 2024 assessment data. Stock levels, supplier delivery times and purchase orders are not provided. Forecasts are estimates, not order requirements."
        )
    st.caption("2024 assessment data · AED · EA")
if not 0 < a < b < 100 or not 0 <= x < y:
    st.error("Set thresholds to 0 < A < B < 100 and 0 ≤ X < Y.")
    st.stop()
filtered = filter_data(data, selections, selected_months)
filtered.attrs["entity_catalog"] = {
    column: data[column].unique().tolist()
    for column in ["product", "brand", "division", "category"]
}
thresholds = (a, b, x, y)
scope = hashlib.sha256(payload).hexdigest() + str(selections) + str(selected_months)
if page == "SupplyIQ assistant":
    st.session_state["assistant_dialog_open"] = False
dialog_requested = st.session_state.get("assistant_dialog_open", False)
ordered = sorted(selected_months)
period = "No months selected"
if ordered:
    period = (
        (ordered[0].strftime("%b") + "–" + ordered[-1].strftime("%b %Y"))
        if len(ordered) > 1
        and all(
            ordered[i] + pd.offsets.MonthBegin(1) == ordered[i + 1]
            for i in range(len(ordered) - 1)
        )
        else ", ".join(month.strftime("%b %Y") for month in ordered)
    )
st.caption(
    f"{period}  ·  {len(filtered):,} transactions  ·  {filtered['product'].nunique()} SKUs  ·  All panels use these filters"
)
extra = [
    f"{column.replace('_', ' ').title()}: {', '.join(st.session_state.get('filter_' + column, []))}"
    for column in DIMENSIONS[3:]
    if st.session_state.get("filter_" + column)
]
if extra:
    st.caption("Additional filters · " + " | ".join(extra))
if len(selected_months) < 12:
    st.caption(
        "Partial-year selection. Annual monthly average still divides selected units by 12."
    )
source_months = pd.DatetimeIndex(sorted(data.month.unique()))
missing_selected = pd.DatetimeIndex(selected_months).difference(source_months)
if report.get("missing_calendar_months", "None") != "None":
    st.warning(
        "Source coverage needs review. The workbook has no records for "
        + report["missing_calendar_months"]
        + ". We cannot confirm whether these months had no sales or are missing from the file."
    )
if len(missing_selected) and page != "Data quality & downloads":
    st.session_state["assistant_dialog_open"] = False
    st.session_state.pop("assistant_pending_question", None)
    st.info(
        "Choose months present in the workbook before analysing demand. Months without sales for an individual product still count as zero when the source month is present."
    )
    st.button(
        "Use available months",
        on_click=use_available_months,
        args=(source_months.tolist(),),
        type="primary",
    )
    st.stop()
if filtered.empty:
    st.session_state["assistant_dialog_open"] = False
    st.session_state.pop("assistant_pending_question", None)
    st.info(
        "No transactions match the selected filters. Choose at least one month or broaden the dimension filters."
    )
    st.button("Restore full-year view", on_click=reset_filters, type="primary")
    if page == "Data quality & downloads":
        views.quality(data, report, filtered, selected_months)
    st.stop()
if page == "Executive overview":
    reference_data = (
        filter_data(data, selections, MONTHS)
        if st.session_state.get("overview_compare", False)
        else filtered
    )
    views.overview(
        filtered,
        selected_months,
        reference_data=reference_data,
        thresholds=thresholds,
        scope=scope,
        available_months=source_months,
    )
elif page == "SKU analysis":
    views.intelligence(filtered, selected_months, thresholds)
elif page == "Demand forecasting":
    views.forecasting(filtered, selected_months)
elif page == "SupplyIQ assistant":
    views.assistant(filtered, selected_months, thresholds, scope)
else:
    views.quality(data, report, filtered, selected_months)
st.divider()
st.caption(
    "SupplyIQ · Sales history only: stock and supplier data are not provided. Forecasts are estimates, not purchase requirements."
)

if page != "SupplyIQ assistant":
    st.button(
        "Ask SupplyIQ",
        key="assistant_fab",
        icon=":material/chat:",
        on_click=open_assistant,
        type="primary",
    )
if dialog_requested and page != "SupplyIQ assistant":
    supplyiq_chat_dialog()

if page != "SupplyIQ assistant":
    with st.expander("New here? Start with a planning question"):
        st.write(
            "1. Choose your filters in the sidebar. 2. Explore a question below. 3. Download the supporting results. Hover over charts for exact values; use chart controls to zoom or reset."
        )
        shortcuts = st.columns(3)
        for column, label, destination in zip(
            shortcuts,
            ["Explore priority SKUs", "Try a demand scenario", "Ask SupplyIQ"],
            [
                "SKU analysis",
                "Demand forecasting",
                "SupplyIQ assistant",
            ],
        ):
            column.button(
                label,
                on_click=open_assistant
                if destination == "SupplyIQ assistant"
                else navigate,
                args=() if destination == "SupplyIQ assistant" else (destination,),
                width="stretch",
            )
