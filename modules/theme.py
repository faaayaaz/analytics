"""Visual system: responsive cards, navigation states and restrained motion."""

import streamlit as st


def apply_theme():
    st.markdown(
        """<style>
.stApp {background:radial-gradient(ellipse at 88% 0%,#e5f3f0 0%,transparent 42%),#f6f8fc;}
.block-container {padding-top:1.5rem;padding-bottom:2rem;max-width:1600px;}
h1,h2,h3 {letter-spacing:-.035em;}
[data-testid="stSidebar"] {background:linear-gradient(170deg,#102138 0%,#16374b 65%,#16565b 100%);border-right:1px solid #16314d12;}
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
.hero {position:relative;overflow:hidden;background:linear-gradient(110deg,#10263e 5%,#174b60 78%,#126e72);padding:30px 34px;border-radius:22px;margin-bottom:18px;color:white;box-shadow:0 14px 38px #17345420;}
.hero::after {content:'';position:absolute;right:-65px;top:-95px;width:275px;height:275px;border:40px solid #ffffff08;border-radius:50%;pointer-events:none;}
.hero h1 {color:white;font-size:32px;font-weight:750;line-height:1.2;padding:0;margin:10px 0;}
.hero p {color:#c4e5e5;margin:0;font-size:14px;}
.hero-divider {padding:0 9px;color:#72b5bb;}
.hero-tags {display:flex;gap:8px;flex-wrap:wrap;margin-top:20px;}
.hero-tags span {font-size:11px;letter-spacing:.2px;color:#d5eeed;background:#ffffff0b;border:1px solid #ffffff22;border-radius:100px;padding:6px 11px;}
.st-key-assistant_launcher {background:linear-gradient(110deg,#ffffff,#edf8f6);border-color:#cce5e0;border-radius:15px;box-shadow:0 3px 12px #12344d05;}
.st-key-assistant_launcher [data-testid="stCaptionContainer"],.st-key-assistant_launcher [data-testid="stCaptionContainer"] * {color:#526e7b;}
[data-testid="stSidebar"] [data-testid="stTooltipIcon"] svg {color:#b6d9dc;}
.eyebrow {font-size:11px;letter-spacing:2px;color:#89ded4;font-weight:700;}
[data-testid="stMetricLabel"] p {white-space:normal;font-size:12px;font-weight:600;color:#526b82;}
[data-testid="stMetricValue"] {font-size:29px;font-weight:650;letter-spacing:-.04em;color:#142f49;}
[class*="st-key-kpi_card_"] {position:relative;background:white;border-radius:16px;border-color:#e1e8f0;box-shadow:0 3px 12px #17345405;transition:transform .18s,box-shadow .18s,border-color .18s;}
[class*="st-key-kpi_card_"]:hover {transform:translateY(-3px);box-shadow:0 9px 24px #16314d14;border-color:#3dbdb5;}
[class*="st-key-kpi_card_"]::before {content:'';display:block;height:3px;position:absolute;left:18px;right:18px;top:0;border-radius:0 0 4px 4px;background:linear-gradient(90deg,#009e98,#b6e4dc);}
.st-key-kpi_card_1::before,.st-key-kpi_card_5::before {background:linear-gradient(90deg,#4b82b8,#c7dcf0);}
.st-key-kpi_card_2::before,.st-key-kpi_card_6::before {background:linear-gradient(90deg,#7c72aa,#e3dff1);}
.st-key-kpi_card_3::before,.st-key-kpi_card_7::before {background:linear-gradient(90deg,#d5a24f,#f3e6c9);}
[class*="st-key-kpi_card_"] button {font-size:11px;min-height:30px;}
button {transition:box-shadow .18s,transform .18s !important;border-radius:9px !important;}
button:hover {box-shadow:0 4px 12px #17345418;}
button:active {transform:translateY(1px);}
button:focus-visible {outline:3px solid #39bfb5 !important;outline-offset:2px;}
[role="tablist"] {gap:5px;border:1px solid #e1e8f0;border-radius:13px;padding:5px;background:#eaf0f5;margin:12px 0 18px;}
[role="tab"] {border-radius:9px;padding:10px 19px;background:transparent;min-height:42px;}
[role="tab"][aria-selected="true"] {background:white;color:#087a75;font-weight:700;box-shadow:0 2px 6px #18324b0b;}
[data-testid="stPlotlyChart"] {border:1px solid #e1e8f0;border-radius:16px;background:white;padding:10px;box-shadow:0 4px 15px #17345405;}
[data-testid="stDataFrame"] {border-radius:12px;overflow:hidden;}
[data-testid="stAlert"] {border-radius:12px;}
.insight-label {font-size:11px;letter-spacing:1.5px;color:#087d77;font-weight:700;margin-bottom:8px;}
@media(max-width:700px) {.hero {padding:22px;}.hero h1 {font-size:25px;}[data-testid="stMetricValue"] {font-size:25px;}[role="tab"] {padding:9px 10px;font-size:12px;}}
@media(prefers-reduced-motion:reduce) {* {transition:none !important;animation:none !important;}}
</style>""",
        unsafe_allow_html=True,
    )


def focus_metric(name):
    st.session_state["focus_metric"] = name
