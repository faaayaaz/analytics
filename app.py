import hashlib
import streamlit as st
from modules.data_loader import (
    load_workbook,
    filter_data,
    DEFAULT_PATH,
    DIMENSIONS,
    MONTHS,
)
from modules import views

st.set_page_config(
    page_title="Consumer Supply Planning Intelligence", page_icon="◈", layout="wide"
)
st.markdown(
    """<style>
.stApp {background: #f4f7fb;}
[data-testid="stSidebar"] {background: #12283f;}
[data-testid="stSidebar"] * {color: #eef6fc;}
[data-testid="stSidebar"] input {color: #162941;}
[data-testid="stSidebar"] [data-testid="stFileUploader"] * {color: #162941;}
[data-testid="stSidebar"] [data-baseweb="select"] * {color: #162941;}
[data-testid="stSidebar"] [data-baseweb="tag"] * {color: #ffffff;}
[data-testid="stSidebar"] [data-testid="stNumberInput"] input {color: #162941;}
[data-testid="stMetricLabel"] p {white-space: normal;}
[data-testid="stSidebar"] [data-baseweb="tag"] {background:#186b75;}
h1,h2,h3 {letter-spacing:-.025em;}
[data-testid="stMetric"] {background:white; border-top:3px solid #009e98; padding:18px; border-radius:10px;}
[data-testid="stMetricLabel"] {font-size:13px;}
[data-testid="stMetricValue"] {font-size:27px;}
.block-container {padding-top:2rem; padding-bottom:2rem; max-width:1600px;}
.hero {background:linear-gradient(115deg,#12283f,#1c4559);padding:28px 32px;border-radius:14px;margin-bottom:22px;color:white;}
.hero h1 {color:white;font-size:30px;padding:0;margin:0 0 8px 0;}
.hero p {color:#b8deda;margin:0;font-size:15px;}
</style>""",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hero"><h1>Consumer Supply Planning Intelligence</h1><p>Demand Analytics | SKU Prioritization | Forecasting | AI-Powered Insights</p></div>',
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Reading and validating the workbook…", max_entries=3)
def cached_load(payload):
    return load_workbook(payload)


with st.sidebar:
    st.title("◈ SupplyIQ")
    st.caption("CONSUMER PLANNING CONTROL TOWER")
    page = st.radio(
        "Workspace",
        [
            "Executive overview",
            "SKU & demand intelligence",
            "Forecasting & scenario lab",
            "SupplyIQ assistant",
            "Data quality & exports",
        ],
    )
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
    month_labels = {d: d.strftime("%b %Y") for d in MONTHS}
    selected_months = st.multiselect(
        "Month",
        MONTHS.tolist(),
        default=MONTHS.tolist(),
        format_func=lambda d: month_labels[d],
    )
    selections = {}
    available = data
    # Cascading dimensions implement Division → Category → Brand → SKU drilldown.
    for col in DIMENSIONS:
        options = sorted(available[col].unique())
        values = st.multiselect(
            col.replace("_", " ").title(),
            options,
            default=[],
            placeholder="All",
            key="filter_" + col,
        )
        selections[col] = values if values else options
        if values:
            available = available.loc[available[col].isin(values)]
    st.caption(
        "Empty dimension selection = all available values. An empty month selection = no records."
    )
    with st.expander("Classification settings"):
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
    st.caption("2024 assessment data • AED • EA")
if not 0 < a < b < 100 or not 0 <= x < y:
    st.error("Set thresholds to 0 < A < B < 100 and 0 ≤ X < Y.")
    st.stop()
filtered = filter_data(data, selections, selected_months)
thresholds = (a, b, x, y)
st.caption(
    f"SCOPE  |  {len(filtered):,} transactions  ·  {filtered['product'].nunique()} SKUs  ·  {len(selected_months)} months  ·  Source: "
    + ("uploaded workbook" if uploaded else "assessment workbook")
)
st.caption(
    "Sales-based planning intelligence. Inventory, supplier lead times and purchase orders are not provided. Source values are anonymized, scaled and randomized."
)
if filtered.empty:
    st.info(
        "No transactions match the selected filters. Choose at least one month or broaden the dimension filters."
    )
    if page == "Data quality & exports":
        views.quality(data, report, filtered, selected_months)
    st.stop()
if page == "Executive overview":
    views.overview(filtered, selected_months)
elif page == "SKU & demand intelligence":
    views.intelligence(filtered, selected_months, thresholds)
elif page == "Forecasting & scenario lab":
    views.forecasting(filtered, selected_months)
elif page == "SupplyIQ assistant":
    scope = hashlib.sha256(payload).hexdigest() + str(selections) + str(selected_months)
    views.assistant(filtered, selected_months, thresholds, scope)
else:
    views.quality(data, report, filtered, selected_months)
st.divider()
st.caption(
    "SUPPLYIQ  /  Evidence-led demand planning  •  All scenarios are estimates; validate commercial drivers before operational decisions."
)
