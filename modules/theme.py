"""SupplyIQ visual system: midnight navy, electric blue, teal and readable surfaces."""

import streamlit as st


def apply_theme():
    st.markdown(
        """<style>
:root {--iq-navy:#101a30;--iq-blue:#3563ff;--iq-teal:#079c89;--iq-lime:#c6f36b;--iq-muted:#62708a;--iq-border:#e5eaf2;}
.stApp {background:#f4f6fb;color:#17243c;}
.block-container {padding-top:3.1rem;padding-bottom:2rem;max-width:1740px;}
h1,h2,h3 {letter-spacing:-.035em;}
.dashboard-heading {padding:4px 0 12px;}
.dashboard-heading .eyebrow {display:flex;align-items:center;gap:8px;font-size:10px;color:#526581;letter-spacing:2px;font-weight:750;margin-bottom:9px;}
.brand-mark {display:inline-grid;place-items:center;width:23px;height:23px;border-radius:7px;background:var(--iq-blue);color:white;font-size:15px;letter-spacing:0;box-shadow:0 3px 8px #3563ff26;}
.dashboard-heading h1 {font-size:clamp(20px,1.8vw,29px);line-height:1.18;color:var(--iq-navy);font-weight:750;margin:0;padding:0;}
[data-testid="stHeadingWithActionElements"] h2 {font-size:23px;font-weight:720;padding-top:0;}
[data-testid="stHeadingWithActionElements"] h3 {font-size:16px;font-weight:700;padding-top:0;}
[data-testid="stCaptionContainer"] {color:var(--iq-muted);}
[data-testid="stMain"] [data-testid="stCaptionContainer"] p {color:var(--iq-muted);}
/* Sidebar stays dark; input surfaces stay light with readable text. */
[data-testid="stSidebar"] {background:linear-gradient(175deg,#0e172a,#14243c);border-right:1px solid #1f314a;}
[data-testid="stSidebar"] * {color:#dce5f5;}
[data-testid="stSidebar"] h1 {font-size:28px !important;color:white;letter-spacing:-1px;}
[data-testid="stSidebar"] [role="radiogroup"] {gap:6px;}
[data-testid="stSidebar"] [role="radiogroup"] label {width:100%;padding:11px 12px;border:1px solid transparent;border-radius:9px;transition:background .18s;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background:#ffffff0b;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#3563ff24;border-color:#537bff55;box-shadow:inset 3px 0 #7293ff;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * {color:#ffffff;}
[data-testid="stSidebar"] input,[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] *,[data-testid="stSidebar"] [data-baseweb="select"] *,[data-testid="stSidebar"] [data-testid="stNumberInput"] input {color:#17243c;}
[data-testid="stSidebar"] [data-baseweb="tag"] {background:#dce6ff;}
[data-testid="stSidebar"] [data-baseweb="tag"] * {color:#23449b;}
[data-testid="stSidebar"] [data-testid="stButton"] button * {color:#17243c;}
[data-testid="stSidebar"] [data-testid*="Tooltip"],[data-testid="stSidebar"] [data-testid="stTooltipIcon"] svg {color:#b6c9e5;}
[data-testid="stSidebar"] [data-testid="stExpander"] {border-color:#ffffff17;border-radius:10px;background:#ffffff05;}
[data-testid="stSidebar"] button[aria-label^="Help"] svg {color:#b6c9e5 !important;}
/* Data cards: one signature anchor, three financial cards, four compact signals. */
[class*="st-key-kpi_card_"] {position:relative;background:white;border:1px solid var(--iq-border);border-radius:15px;box-shadow:0 3px 10px #17243c03;transition:border-color .18s,box-shadow .18s;}
[class*="st-key-kpi_card_"]:hover {border-color:#a6b9ff;box-shadow:0 8px 22px #17243c0a;}
[class*="st-key-kpi_card_"] [data-testid="stMetric"] {padding:0;}
[data-testid="stMetricLabel"] p {white-space:normal;font-size:11px;font-weight:600;color:#62708a;}
[data-testid="stMetricValue"] {font-size:clamp(21px,2vw,31px);font-weight:750;letter-spacing:-.045em;color:#17243c;font-variant-numeric:tabular-nums;}
.metric-kicker {font-size:9px;letter-spacing:1.6px;text-transform:uppercase;color:#73839e;font-weight:700;margin-bottom:2px;}
.st-key-kpi_card_0 {background:linear-gradient(125deg,#15233e,#233b66);border-color:#243e66;box-shadow:0 8px 20px #13233c20;}
.st-key-kpi_card_0 [data-testid="stMetricValue"],.st-key-kpi_card_0 [data-testid="stMetricLabel"] p {color:#ffffff;}
.st-key-kpi_card_0 .metric-kicker {color:var(--iq-lime);}
.st-key-kpi_card_0 [data-testid*="Tooltip"],.st-key-kpi_card_0 [data-testid="stTooltipIcon"] svg,.st-key-kpi_card_0 button,.st-key-kpi_card_0 button svg {color:#b9c8e1 !important;}
.st-key-kpi_card_1 {border-top:3px solid #3563ff;}
.st-key-kpi_card_2 {border-top:3px solid #0bb49c;}
.st-key-kpi_card_3 {border-top:3px solid #bbdf6a;}
.st-key-kpi_card_4,.st-key-kpi_card_5,.st-key-kpi_card_6,.st-key-kpi_card_7 {background:#edf1f8;box-shadow:none;border-color:#e5ebf5;}
.st-key-kpi_card_4 [data-testid="stMetricValue"],.st-key-kpi_card_5 [data-testid="stMetricValue"],.st-key-kpi_card_6 [data-testid="stMetricValue"],.st-key-kpi_card_7 [data-testid="stMetricValue"] {font-size:21px;}
/* Chart panels use one border, a quiet header and generous plotting space. */
.st-key-dashboard_trend,.st-key-dashboard_divisions,.st-key-dashboard_products,.st-key-dashboard_alerts {background:white;border:1px solid var(--iq-border);border-radius:16px;box-shadow:0 3px 12px #14243c04;}
.st-key-dashboard_trend [data-testid="stPlotlyChart"],.st-key-dashboard_divisions [data-testid="stPlotlyChart"],.st-key-dashboard_products [data-testid="stPlotlyChart"] {border:0;box-shadow:none;padding:0;}
.st-key-dashboard_alerts {background:linear-gradient(155deg,#111e35,#1c3454);border:1px solid #254162;}
.st-key-dashboard_alerts h3,.st-key-dashboard_alerts p {color:#e6edf8;}
.st-key-dashboard_alerts [data-testid="stCaptionContainer"] p {color:#b9c8df;}
.st-key-dashboard_alerts [data-testid="stButton"] button {background:#c6f36b;border-color:#c6f36b;}
.st-key-dashboard_alerts [data-testid="stButton"] button * {color:#172d1c;}
.attention-item {padding:12px 0;border-bottom:1px solid #ffffff18;}
.attention-item:last-child {border-bottom:0;}
.attention-item .attention-index {display:inline-block;color:#c6f36b;font-size:10px;letter-spacing:1.2px;font-weight:700;margin-bottom:5px;}
.attention-item p {font-size:13px;line-height:1.6;margin:0;}
[data-testid="stPlotlyChart"] {background:white;border:1px solid var(--iq-border);border-radius:14px;padding:8px;}
[data-testid="stDataFrame"] {border-radius:12px;overflow:hidden;border:1px solid var(--iq-border);}
button {border-radius:9px !important;transition:background .16s,box-shadow .16s !important;}
button:hover {box-shadow:0 3px 10px #17243c0d;}
button:focus-visible {outline:3px solid #7293ff !important;outline-offset:2px;}
.st-key-open_supplyiq button {background:#3563ff;border-color:#3563ff;box-shadow:0 4px 12px #3563ff24;}
.st-key-open_supplyiq button:hover {background:#254fe0;border-color:#254fe0;}
[role="radiogroup"][aria-label="View"],[role="radiogroup"][aria-label="Division measure"] {background:#f0f3f9;border-radius:8px;padding:3px;}
[role="tablist"] {gap:6px;background:#eaf0f8;padding:5px;border-radius:11px;border:1px solid var(--iq-border);}
[role="tab"] {border-radius:7px;padding:10px 16px;}
[role="tab"][aria-selected="true"] {background:white;color:#3563ff;font-weight:700;box-shadow:0 2px 5px #14243c07;}
[data-testid="stExpander"] {border-radius:11px;border-color:var(--iq-border);background:#ffffff60;}
[data-testid="stAlert"] {border-radius:11px;}
.insight-label {color:#079c89;letter-spacing:1.3px;font-size:10px;font-weight:700;}
@media(max-width:1100px) {.dashboard-heading h1 {font-size:21px;}}
@media(max-width:700px) {
.block-container {padding-top:3rem;}
.dashboard-heading h1 {font-size:22px;}
[data-testid="stHorizontalBlock"]:has(.st-key-kpi_card_0),[data-testid="stHorizontalBlock"]:has(.st-key-kpi_card_4) {flex-wrap:wrap;gap:8px;}
[data-testid="stHorizontalBlock"]:has(.st-key-kpi_card_0)>[data-testid="stColumn"],[data-testid="stHorizontalBlock"]:has(.st-key-kpi_card_4)>[data-testid="stColumn"] {min-width:0 !important;width:calc(50% - 5px) !important;flex:1 1 calc(50% - 5px) !important;}
[class*="st-key-kpi_card_"] [data-testid="stMetricValue"] {font-size:20px !important;}
[class*="st-key-kpi_card_"] [data-testid="stMetricLabel"] p {font-size:10px;}
.metric-kicker {font-size:8px;letter-spacing:1px;}
}
@media(prefers-reduced-motion:reduce) {* {transition:none !important;animation:none !important;}}
</style>""",
        unsafe_allow_html=True,
    )


def focus_metric(name):
    st.session_state["focus_metric"] = name
