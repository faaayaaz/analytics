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

st.set_page_config(
    page_title="Consumer Supply Planning Intelligence", page_icon="◈", layout="wide"
)
from modules.theme import apply_theme

apply_theme()


@st.cache_data(show_spinner="Reading and validating the workbook…", max_entries=3)
def cached_load(payload):
    return load_workbook(payload)


with st.sidebar:
    st.title("◈ SupplyIQ")
    st.caption("SUPPLY PLANNING WORKSPACE")
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
    with st.expander("Upload a different workbook"):
        uploaded = st.file_uploader("Replace assessment workbook", type=["xlsx"])
try:
    payload = uploaded.getvalue() if uploaded else DEFAULT_PATH.read_bytes()
    data, report = cached_load(payload)
except (ValueError, KeyError, OSError, TypeError) as exc:
    st.error(f"Workbook could not be loaded: {exc}")
    st.stop()

with st.sidebar:
    st.divider()
    st.subheader("Global filters")
    st.button(
        "Reset all filters",
        on_click=reset_filters,
        width="stretch",
        key="sidebar_reset",
    )
    p1, p2 = st.columns(2)
    p1.button("Full year", on_click=set_period, args=(0,), width="stretch")
    p2.button("Q4 only", on_click=set_period, args=(9,), width="stretch")
    month_labels = {d: d.strftime("%b %Y") for d in MONTHS}
    st.session_state.setdefault("filter_months", MONTHS.tolist())
    with st.expander("Select individual months"):
        selected_months = st.multiselect(
            "Month",
            MONTHS.tolist(),
            key="filter_months",
            help="Select the months to analyze. Full year is recommended for classification and forecasting.",
            format_func=lambda d: month_labels[d],
        )
    selections = {}
    available = data
    # Cascading dimensions implement Division → Category → Brand → SKU drilldown.
    advanced_filters = None
    for col in DIMENSIONS:
        options = sorted(available[col].unique())
        # Remove invalid downstream selections when a parent drilldown changes.
        state_key = "filter_" + col
        if state_key in st.session_state:
            st.session_state[state_key] = [
                v for v in st.session_state[state_key] if v in options
            ]
        if col == "product":
            advanced_filters = st.expander("More filters: SKU, customer & market")
        filter_container = (
            st.container()
            if col in ["division", "category", "brand"]
            else advanced_filters
        )
        with filter_container:
            values = st.multiselect(
                col.replace("_", " ").title(),
                options,
                placeholder="All",
                key=state_key,
                help="Type to search. Leave empty to include all available values. Choices follow the filters above.",
            )
        selections[col] = values if values else options
        if values:
            available = available.loc[available[col].isin(values)]
    st.caption(
        "Empty dimension selection = all available values. An empty month selection = no records."
    )
    with st.expander("Quick word guide"):
        st.markdown(
            "**SKU:** a product code. **Net sales:** sales after returns and credit notes. **Net demand:** units sold minus returns. **ABC:** groups products by sales value. **XYZ:** groups them by how steady demand is. **CV:** a score for changes in demand; lower means steadier. **Forecast:** an estimate of future demand. **N/A:** cannot be calculated from this selection."
        )
    with st.expander("Classification settings"):
        st.caption(
            "Choose the sales cutoffs for ABC and the demand-change scores for XYZ."
        )
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
            "X maximum CV",
            min_value=0.0,
            max_value=5.0,
            value=0.5,
            step=0.1,
        )
        y = st.number_input(
            "Y maximum CV",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1,
        )
    st.caption("2024 assessment data • AED • EA")
if not 0 < a < b < 100 or not 0 <= x < y:
    st.error("Set thresholds to 0 < A < B < 100 and 0 ≤ X < Y.")
    st.stop()
filtered = filter_data(data, selections, selected_months)
thresholds = (a, b, x, y)
heading, assistant_button, summary_button = st.columns(
    [4.5, 1.1, 1.5], vertical_alignment="center"
)
with heading:
    st.markdown(
        '<div class="dashboard-heading"><div class="eyebrow">SUPPLYIQ / CONSUMER PLANNING</div><h1>Consumer Supply Planning Intelligence</h1></div>',
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
        disabled=filtered.empty,
        width="stretch",
    )

ordered_months = sorted(selected_months)
period = "No months selected"
if ordered_months:
    period = (
        (ordered_months[0].strftime("%b") + "–" + ordered_months[-1].strftime("%b %Y"))
        if len(ordered_months) > 1
        and all(
            ordered_months[i] + pd.offsets.MonthBegin(1) == ordered_months[i + 1]
            for i in range(len(ordered_months) - 1)
        )
        else ", ".join(month.strftime("%b %Y") for month in ordered_months)
    )
st.caption("PERIOD: " + period)
st.caption(
    f"YOUR SELECTION  ·  {len(filtered):,} transactions  ·  {filtered['product'].nunique()} SKUs  ·  {len(selected_months)} months  ·  "
    + ("uploaded workbook" if uploaded else "assessment workbook")
)
with st.sidebar:
    with st.expander("About this data"):
        st.write(
            "This assessment uses anonymized sales data with adjusted values. It does not include inventory, supplier delivery times or purchase orders. Use the results to review demand, not to decide order quantities on their own."
        )
active = [
    f"{column.replace('_', ' ').title()}: {', '.join(st.session_state.get('filter_' + column, []))}"
    for column in DIMENSIONS
    if st.session_state.get("filter_" + column)
]
if active:
    st.caption("Active filters · " + " | ".join(active))
if len(selected_months) < 12:
    st.caption(
        "You selected part of the year. Months you left out are not counted as zero demand. The annual monthly average still divides selected units by 12."
    )
if filtered.empty:
    st.info(
        "No transactions match the selected filters. Choose at least one month or broaden the dimension filters."
    )
    st.button("Restore full-year view", on_click=reset_filters, type="primary")
    if page == "Data quality & downloads":
        views.quality(data, report, filtered, selected_months)
    st.stop()
if page == "Executive overview":
    views.overview(filtered, selected_months)
elif page == "SKU analysis":
    views.intelligence(filtered, selected_months, thresholds)
elif page == "Demand forecasting":
    views.forecasting(filtered, selected_months)
elif page == "SupplyIQ assistant":
    scope = hashlib.sha256(payload).hexdigest() + str(selections) + str(selected_months)
    views.assistant(filtered, selected_months, thresholds, scope)
else:
    views.quality(data, report, filtered, selected_months)
st.divider()
st.caption(
    "SupplyIQ · Sales history only: stock and supplier data are not provided. Forecasts are estimates, not purchase requirements."
)

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
        column.button(label, on_click=navigate, args=(destination,), width="stretch")
