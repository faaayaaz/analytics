"""Visual system: responsive cards, navigation states and restrained motion."""

import streamlit as st


def apply_theme():
    st.markdown(
        """<style>
.stApp {background:#f3f6fb;}
.block-container {padding-top:1.8rem;padding-bottom:2rem;max-width:1600px;}
h1,h2,h3 {letter-spacing:-.035em;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#10263e,#173d50);}
[data-testid="stSidebar"] * {color:#e6f0f8;}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] *,
[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-testid="stNumberInput"] input {color:#162941;}
[data-testid="stSidebar"] [data-testid="stFileUploader"] > label * {color:#e6f0f8;}
[data-testid="stSidebar"] [data-testid="stButton"] button * {color:#162941;}
[data-testid="stSidebar"] [data-baseweb="tag"] {background:#147d80;}
[data-testid="stSidebar"] [data-baseweb="tag"] * {color:white;}
[data-testid="stSidebar"] [role="radiogroup"] {gap:7px;}
[data-testid="stSidebar"] [role="radiogroup"] label {width:100%;padding:11px 12px;border-radius:9px;border:1px solid #ffffff14;transition:background .18s,transform .18s;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background:#ffffff14;transform:translateX(3px);}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#168b8b40;border-color:#45c9c2;}
.hero {position:relative;overflow:hidden;background:linear-gradient(110deg,#10263e 5%,#174b60 78%,#126e72);padding:30px 34px;border-radius:18px;margin-bottom:20px;color:white;box-shadow:0 12px 32px #17345412;}
.hero::after {content:'';position:absolute;right:-65px;top:-95px;width:275px;height:275px;border:40px solid #ffffff08;border-radius:50%;pointer-events:none;}
.hero h1 {color:white;font-size:30px;padding:0;margin:8px 0;}
.hero p {color:#c4e5e5;margin:0;font-size:14px;}
.eyebrow {font-size:11px;letter-spacing:2px;color:#89ded4;font-weight:700;}
[data-testid="stMetricLabel"] p {white-space:normal;font-size:12px;font-weight:600;color:#61758b;}
[data-testid="stMetricValue"] {font-size:27px;letter-spacing:-.04em;color:#16314d;}
[class*="st-key-kpi_card_"] {background:white;border-radius:14px;transition:transform .18s,box-shadow .18s,border-color .18s;}
[class*="st-key-kpi_card_"]:hover {transform:translateY(-3px);box-shadow:0 9px 24px #16314d14;border-color:#3dbdb5;}
[class*="st-key-kpi_card_"] button {font-size:11px;min-height:30px;}
button {transition:box-shadow .18s,transform .18s !important;border-radius:9px !important;}
button:hover {box-shadow:0 4px 12px #17345418;}
button:active {transform:translateY(1px);}
button:focus-visible {outline:3px solid #39bfb5 !important;outline-offset:2px;}
[role="tablist"] {gap:9px;border-bottom:1px solid #dbe5ef;padding:4px 0 10px;}
[role="tab"] {border-radius:8px;padding:10px 17px;background:white;}
[role="tab"][aria-selected="true"] {background:#dff4ef;color:#087a75;font-weight:700;}
[data-testid="stPlotlyChart"] {border:1px solid #e1e8f0;border-radius:14px;background:white;padding:8px;}
[data-testid="stDataFrame"] {border-radius:12px;overflow:hidden;}
.insight-label {font-size:11px;letter-spacing:1.5px;color:#087d77;font-weight:700;margin-bottom:8px;}
@media(max-width:700px) {.hero {padding:22px;}.hero h1 {font-size:25px;}[data-testid="stMetricValue"] {font-size:25px;}[role="tab"] {padding:9px 10px;font-size:12px;}}
@media(prefers-reduced-motion:reduce) {* {transition:none !important;animation:none !important;}}
</style>""",
        unsafe_allow_html=True,
    )


def focus_metric(name):
    st.session_state["focus_metric"] = name
