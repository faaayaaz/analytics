"""SupplyIQ visual system: tailored navy, muted gold and warm neutral surfaces."""

import streamlit as st


def apply_theme():
    st.markdown(
        """<style>
:root {--iq-navy:#14253D;--iq-gold:#B99146;--iq-accent:#B99146;--iq-gold-light:#D9BE82;--iq-muted:#687486;--iq-border:#E5E2D9;}
.stApp {background:#F7F6F2;color:#14253D;}
.block-container {padding-top:3.1rem;padding-bottom:2rem;max-width:1740px;}
h1,h2,h3 {letter-spacing:-.035em;}
.dashboard-heading {padding:4px 0 12px;}
.dashboard-heading .eyebrow {display:flex;align-items:center;gap:8px;font-size:10px;color:#687486;letter-spacing:2px;font-weight:750;margin-bottom:9px;}
.brand-mark {display:inline-grid;place-items:center;width:23px;height:23px;border-radius:7px;background:var(--iq-gold-light);color:var(--iq-navy);font-size:15px;letter-spacing:0;box-shadow:0 3px 8px #B9914626;}
.dashboard-heading h1 {font-size:clamp(20px,1.8vw,29px);line-height:1.18;color:var(--iq-navy);font-weight:750;margin:0;padding:0;}
[data-testid="stHeadingWithActionElements"] h2 {font-size:23px;font-weight:720;padding-top:0;}
[data-testid="stHeadingWithActionElements"] h3 {font-size:16px;font-weight:700;padding-top:0;}
[data-testid="stCaptionContainer"] {color:var(--iq-muted);}
[data-testid="stMain"] [data-testid="stCaptionContainer"] p {color:var(--iq-muted);}
/* Sidebar stays dark; input surfaces stay light with readable text. */
[data-testid="stSidebar"] {background:linear-gradient(175deg,#0E1A2D,#14253D);border-right:1px solid #2B3A50;}
[data-testid="stSidebar"] * {color:#E2E5E9;}
[data-testid="stSidebar"] h1 {font-size:28px !important;color:white;letter-spacing:-1px;}
[data-testid="stSidebar"] [role="radiogroup"] {gap:6px;}
[data-testid="stSidebar"] [role="radiogroup"] label {width:100%;padding:11px 12px;border:1px solid transparent;border-radius:9px;transition:background .18s;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background:#ffffff0b;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#B9914624;border-color:#B9914660;box-shadow:inset 3px 0 #C4A15C;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * {color:#ffffff;}
[data-testid="stSidebar"] input,[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] *,[data-testid="stSidebar"] [data-baseweb="select"] *,[data-testid="stSidebar"] [data-testid="stNumberInput"] input {color:#14253D;}
[data-testid="stSidebar"] [data-baseweb="tag"] {background:#F1E7D2;}
[data-testid="stSidebar"] [data-baseweb="tag"] * {color:#675022;}
[data-testid="stSidebar"] [data-testid="stButton"] button * {color:#14253D;}
[data-testid="stSidebar"] [data-testid*="Tooltip"],[data-testid="stSidebar"] [data-testid="stTooltipIcon"] svg {color:#b6c9e5;}
[data-testid="stSidebar"] [data-testid="stExpander"] {border-color:#ffffff17;border-radius:10px;background:#ffffff05;}
[data-testid="stSidebar"] button[aria-label^="Help"] svg {color:#b6c9e5 !important;}
/* Data cards: one signature anchor, three financial cards, four compact signals. */
[class*="st-key-kpi_card_"] {position:relative;background:white;border:1px solid var(--iq-border);border-radius:15px;box-shadow:0 3px 10px #14253D03;transition:border-color .18s,box-shadow .18s;}
[class*="st-key-kpi_card_"]:hover {border-color:#CFB781;box-shadow:0 8px 22px #14253D0a;}
[class*="st-key-kpi_card_"] [data-testid="stMetric"] {padding:0;}
[data-testid="stMetricLabel"] p {white-space:normal;font-size:11px;font-weight:600;color:#687486;}
[data-testid="stMetricValue"] {font-size:clamp(21px,2vw,31px);font-weight:750;letter-spacing:-.045em;color:#14253D;font-variant-numeric:tabular-nums;}
.metric-kicker {font-size:9px;letter-spacing:1.6px;text-transform:uppercase;color:#73839e;font-weight:700;margin-bottom:2px;}
.st-key-kpi_card_0 {background:linear-gradient(125deg,#14253D,#233B53);border-color:#30445B;box-shadow:0 8px 20px #14253D20;}
.st-key-kpi_card_0 [data-testid="stMetricValue"],.st-key-kpi_card_0 [data-testid="stMetricLabel"] p {color:#ffffff;}
.st-key-kpi_card_0 .metric-kicker {color:var(--iq-gold-light);}
.st-key-kpi_card_0 [data-testid="stMetricDelta"] {background:#ffffff12;color:#D9BE82 !important;}
.st-key-kpi_card_0 [data-testid="stMetricDelta"] * {color:#D9BE82 !important;}
.st-key-kpi_card_0 [data-testid*="Tooltip"],.st-key-kpi_card_0 [data-testid="stTooltipIcon"] svg,.st-key-kpi_card_0 button,.st-key-kpi_card_0 button svg,.st-key-kpi_card_0 [role="button"],.st-key-kpi_card_0 [role="button"] * {color:#b9c8e1 !important;}
.st-key-kpi_card_1 {border-top:3px solid #B99146;}
.st-key-kpi_card_2 {border-top:3px solid #C4A15C;}
.st-key-kpi_card_3 {border-top:3px solid #D9BE82;}
.st-key-kpi_card_4,.st-key-kpi_card_5,.st-key-kpi_card_6,.st-key-kpi_card_7 {background:#F0EFEA;box-shadow:none;border-color:#E5E2D9;}
.st-key-kpi_card_4 [data-testid="stMetricValue"],.st-key-kpi_card_5 [data-testid="stMetricValue"],.st-key-kpi_card_6 [data-testid="stMetricValue"],.st-key-kpi_card_7 [data-testid="stMetricValue"] {font-size:21px;}
/* One gold trim ties the navy anchor to the light KPI cards. */
.st-key-kpi_card_0 {border-top:2px solid var(--iq-gold);}
.js-plotly-plot .modebar {border:1px solid #E5E2D9;border-radius:7px;padding:2px !important;}
/* Chart panels use one border, a quiet header and generous plotting space. */
.st-key-dashboard_trend,.st-key-dashboard_divisions,.st-key-dashboard_products,.st-key-dashboard_alerts {background:white;border:1px solid var(--iq-border);border-radius:16px;box-shadow:0 3px 12px #14253D04;}
.st-key-dashboard_trend [data-testid="stPlotlyChart"],.st-key-dashboard_divisions [data-testid="stPlotlyChart"],.st-key-dashboard_products [data-testid="stPlotlyChart"] {border:0;box-shadow:none;padding:0;}
.st-key-dashboard_alerts [data-testid="stVerticalBlock"] {gap:10px;}
.st-key-dashboard_alerts {background:linear-gradient(155deg,#14253D,#233B53);border:1px solid #3D4A59;}
.st-key-dashboard_alerts h3,.st-key-dashboard_alerts p {color:#F1F0EB;}
.st-key-dashboard_alerts [data-testid="stCaptionContainer"] p {color:#C2CAD5;}
.st-key-dashboard_alerts [data-testid="stButton"] button {background:#D9BE82;border-color:#D9BE82;}
.st-key-dashboard_alerts [data-testid="stButton"] button * {color:#14253D;}
.attention-item {padding:8px 0;border-bottom:1px solid #ffffff18;}
.attention-item:last-child {border-bottom:0;}
.attention-item .attention-index {display:inline-block;color:#D9BE82;font-size:10px;letter-spacing:1.2px;font-weight:700;margin-bottom:5px;}
.attention-item p {font-size:12px;line-height:1.5;margin:4px 0 0;}
.attention-value {display:block;color:white;font-size:23px;font-weight:700;line-height:1.2;margin:2px 0;}
.st-key-global_filter_bar {background:white;border:1px solid var(--iq-border);border-radius:12px;box-shadow:none;}
.st-key-global_filter_bar [data-testid="stVerticalBlock"] {gap:8px;}
.st-key-dashboard_trend [data-testid="stVerticalBlock"],.st-key-dashboard_divisions [data-testid="stVerticalBlock"],.st-key-dashboard_products [data-testid="stVerticalBlock"] {gap:10px;}
[data-testid="stPlotlyChart"] {background:white;border:1px solid var(--iq-border);border-radius:14px;padding:8px;}
[data-testid="stDataFrame"] {border-radius:12px;overflow:hidden;border:1px solid var(--iq-border);}
/* Planning-page metric tiles and review controls. Overview anchors/dialogs are excluded. */
[data-testid="stMain"] [data-testid="stMetric"]:not([class*="st-key-kpi_card_"] [data-testid="stMetric"]):not([role="dialog"] [data-testid="stMetric"]) {background:white;border-color:var(--iq-border);border-radius:12px;padding:14px 16px;min-height:104px;box-shadow:0 2px 8px #14253D03;}
[data-testid="stMain"] [data-testid="stMetric"]:not([class*="st-key-kpi_card_"] [data-testid="stMetric"]):not([role="dialog"] [data-testid="stMetric"]) [data-testid="stMetricLabel"] p {line-height:1.4;min-height:28px;}
:is(.st-key-workbench_abc,.st-key-workbench_xyz,.st-key-workbench_focus,.st-key-workbench_sort,.st-key-forecast_entity_product,.st-key-forecast_entity_category) [data-baseweb="select"]>div {background:white;border-color:var(--iq-border);border-radius:9px;min-height:40px;}
.st-key-sku_search [data-baseweb="input"] {background:white;border-color:var(--iq-border);border-radius:9px;}
:is(.st-key-workbench_abc,.st-key-workbench_xyz,.st-key-workbench_focus,.st-key-workbench_sort,.st-key-forecast_entity_product,.st-key-forecast_entity_category):focus-within [data-baseweb="select"],.st-key-sku_search:focus-within [data-baseweb="input"] {outline:2px solid var(--iq-gold-light);outline-offset:2px;}
[class*="st-key-sku_workbench_"] [data-testid="stDataFrame"]:focus-within {outline:2px solid var(--iq-gold-light);outline-offset:2px;}
:is(.st-key-workbench_export,.st-key-forecast_review_pack) button:not(:disabled) {background:#F1E7D2;border-color:var(--iq-gold);font-weight:600;}
:is(.st-key-workbench_export,.st-key-forecast_review_pack) button:not(:disabled) * {color:var(--iq-navy);}
:is(.st-key-workbench_export,.st-key-forecast_review_pack) button:not(:disabled):hover {background:var(--iq-gold-light);}
.st-key-scenario_pct [role="slider"]:focus-visible {outline:3px solid var(--iq-gold-light);outline-offset:3px;}
button {border-radius:9px !important;transition:background .16s,box-shadow .16s !important;}
button:hover {box-shadow:0 3px 10px #14253D0D;}
button[kind="primary"] {background:#14253D;border-color:#14253D;}
button[kind="primary"]:hover {background:#294464;border-color:#294464;}
button:focus-visible {outline:3px solid #C4A15C !important;outline-offset:2px;}
.st-key-open_supplyiq button {background:#14253D;border-color:#14253D;box-shadow:0 4px 12px #B9914624;}
.st-key-open_supplyiq button:hover {background:#294464;border-color:#294464;}
[role="radiogroup"][aria-label="View"],[role="radiogroup"][aria-label="Division measure"] {background:#F1EFE8;border-radius:8px;padding:3px;}
[role="tablist"] {gap:6px;background:#F1EFE8;padding:5px;border-radius:11px;border:1px solid var(--iq-border);}
[role="tab"] {border-radius:7px;padding:10px 16px;}
[role="tab"][aria-selected="true"] {background:white;color:#675022;font-weight:700;box-shadow:0 2px 5px #14253D07;}
[data-testid="stExpander"] {border-radius:11px;border-color:var(--iq-border);background:#ffffff60;}
[data-testid="stAlert"] {border-radius:11px;}
.insight-label {color:#B99146;letter-spacing:1.3px;font-size:10px;font-weight:700;}
.st-key-assistant_fab {position:fixed;bottom:22px;right:24px;z-index:900;width:170px !important;max-width:170px;}
.st-key-assistant_fab button {box-shadow:0 8px 24px #14253D2b;border:1px solid #B99146;min-height:46px;}
.assistant-welcome {text-align:center;padding:28px 15px 20px;}
.assistant-emblem {display:inline-grid;place-items:center;width:46px;height:46px;border-radius:14px;background:#F1E7D2;color:#806027;font-size:28px;}
.st-key-supplyiq_dialog_conversation .assistant-welcome {padding:8px 8px 12px;}
.st-key-supplyiq_dialog_conversation .assistant-emblem {width:34px;height:34px;font-size:23px;}
.st-key-supplyiq_dialog_conversation .assistant-welcome h2 {font-size:21px;margin:8px 0 4px;}
.st-key-supplyiq_dialog_conversation .assistant-welcome p {font-size:12px;line-height:1.4;}
.assistant-welcome h2 {font-size:24px;margin:14px 0 7px;color:#14253D;}
.assistant-welcome p {font-size:14px;color:#687486;max-width:420px;margin:0 auto;line-height:1.5;}
[role="dialog"] {border:1px solid #E5E2D9;border-radius:18px;}
[role="dialog"] [data-testid="stChatInput"] {border-color:#B99146;}
[class*="supplyiq_dialog_conversation"],[class*="supplyiq_page_conversation"] {background:white;border-color:#E5E2D9;border-radius:12px;}
@media(max-width:700px) {
.st-key-supplyiq_dialog_conversation [data-testid="stHorizontalBlock"] {flex-wrap:wrap;gap:8px;}
.st-key-supplyiq_dialog_conversation [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {width:calc(50% - 4px) !important;flex:1 1 calc(50% - 4px) !important;min-width:0 !important;}
.st-key-supplyiq_dialog_conversation .assistant-welcome {padding:4px 4px 6px;}
.st-key-supplyiq_dialog_conversation .assistant-emblem {width:28px;height:28px;font-size:20px;}
.st-key-supplyiq_dialog_conversation .assistant-welcome h2 {font-size:19px;margin:5px 0 3px;}
.st-key-supplyiq_dialog_conversation button p {font-size:12px;}
.st-key-supplyiq_dialog_conversation button {padding:6px 8px;}
.st-key-supplyiq_dialog_toolbar [data-testid="stHorizontalBlock"] {flex-wrap:wrap;gap:8px;}
.st-key-supplyiq_dialog_toolbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {width:100% !important;flex:1 1 100% !important;min-width:0 !important;}
.st-key-supplyiq_dialog_toolbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:not(:first-child) {width:calc(50% - 4px) !important;flex:1 1 calc(50% - 4px) !important;min-width:0 !important;}
.st-key-assistant_fab {right:14px;bottom:14px;width:155px !important;}.assistant-welcome {padding:12px 8px;}.st-key-supplyiq_dialog_conversation .assistant-welcome {padding:8px 8px 12px;}
.st-key-supplyiq_dialog_conversation .assistant-emblem {width:34px;height:34px;font-size:23px;}
.st-key-supplyiq_dialog_conversation .assistant-welcome h2 {font-size:21px;margin:8px 0 4px;}
.st-key-supplyiq_dialog_conversation .assistant-welcome p {font-size:12px;line-height:1.4;}
.assistant-welcome h2 {font-size:20px;}}
@media(max-width:1100px) {.dashboard-heading h1 {font-size:21px;}}
@media(max-width:700px) {
.st-key-global_filter_bar [data-testid="stHorizontalBlock"] {flex-wrap:wrap;gap:12px;}
.st-key-global_filter_bar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {min-width:0 !important;width:calc(50% - 6px) !important;flex:1 1 calc(50% - 6px) !important;}
.st-key-global_filter_bar button p {font-size:11px;}
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
