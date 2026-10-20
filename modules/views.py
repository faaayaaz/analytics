import hashlib
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from .kpi_calculations import kpis, monthly_demand, group_summary, executive_insights
from .abc_xyz_analysis import classify, RECOMMENDATIONS
from .forecasting import forecast
from .ai_assistant import answer, FOLLOWUPS
from .usability import set_scenario
from .theme import focus_metric
from .visualizations import show, line, bar

DEFINITIONS = {
    "Net Sales (AED)": "Sum of signed net sales values; includes credits and returns.",
    "Net Units Sold": "Sum of signed quantities in EA. EA does not standardize pack size across products.",
    "Gross Profit (AED)": "Net sales minus signed cost of sales.",
    "Gross Margin %": "Gross profit / net sales × 100. N/A when net sales is zero. Negative-sales margins retain the signed formula and require careful interpretation.",
    "MoM Demand Growth %": "Latest selected month versus the immediately preceding calendar month, only when both are selected and previous demand is positive.",
    "Active SKUs": "Distinct products with at least one transaction in the selection (including return-only or net-zero products).",
    "Average Monthly Net Demand": "Selected signed quantity / 12. This is an annualized selected contribution, not a selected-month mean when months are excluded.",
    "Negative Transaction Quantity Rate %": "Absolute negative quantities / positive quantities × 100. N/A if no positive quantities.",
}


def csv_download(label, data, name, key):
    st.download_button(
        label,
        data.to_csv(index=False).encode("utf-8-sig"),
        file_name=name,
        mime="text/csv",
        key=key,
    )


def overview(data, months):
    st.header("Executive overview")
    st.caption(
        "Performance, demand movement and planning attention • every figure reflects the sidebar scope"
    )
    metrics = kpis(data, months)
    m = monthly_demand(data, sorted(months))
    history = pd.DataFrame(
        [kpis(data.loc[data.month == month], [month]) for month in m.month]
    )
    history["month"] = m.month.to_numpy()
    history["MoM Demand Growth %"] = m.growth_pct.to_numpy()
    for i in range(1, len(m)):
        if m.month.iloc[i] - pd.offsets.MonthBegin(1) != m.month.iloc[i - 1]:
            history.loc[i, "MoM Demand Growth %"] = np.nan
    focused = st.session_state.get("focus_metric", "Net Sales (AED)")
    for offset in [0, 4]:
        cols = st.columns(4)
        for i, (col, (name, value)) in enumerate(
            zip(cols, list(metrics.items())[offset : offset + 4]), start=offset
        ):
            with col, st.container(border=True, key=f"kpi_card_{i}"):
                display = (
                    "N/A"
                    if pd.isna(value)
                    else f"{value:,.2f}%"
                    if "%" in name
                    else f"{value:,.0f}"
                )
                spark = history[name].dropna().tolist()
                st.metric(
                    name,
                    display,
                    help=DEFINITIONS[name],
                    chart_data=spark or None,
                    chart_type="line",
                )
                st.button(
                    "Viewing trend" if focused == name else "Explore trend",
                    key=f"focus_{i}",
                    on_click=focus_metric,
                    args=(name,),
                    width="stretch",
                    type="primary" if focused == name else "secondary",
                )
    st.caption(
        "Select Explore trend on a card to change the chart. Mini charts show the selected monthly history; hover over the ⓘ beside a KPI for its definition."
    )
    performance, business_mix, growth_tab = st.tabs(
        ["Performance studio", "Business mix", "Growth & insights"]
    )
    with performance:
        heading, control = st.columns([3, 1])
        with heading:
            st.subheader(focused)
            st.caption("Monthly view within your selected scope")
        with control:
            style = st.segmented_control(
                "Chart style",
                ["Line", "Area"],
                default="Area",
                key="overview_chart_style",
            )
        plot = (
            px.area(
                history,
                x="month",
                y=focused,
                markers=True,
                title="Selected KPI • monthly history",
            )
            if style == "Area"
            else line(history, "month", focused, "Selected KPI • monthly history")
        )
        plot.update_traces(line_color="#009e98")
        show(
            plot,
            key="focused_metric_chart",
            help_text=DEFINITIONS[focused]
            + " This graph shows that measure separately for each included month. The card above summarizes the full selection. For average monthly net demand, each point is that month’s contribution divided by 12; for growth, only adjacent selected months with a positive prior value are valid.",
        )
        l, r = st.columns(2)
        with l:
            show(line(m, "month", "sales", "Monthly net sales • AED"))
        with r:
            show(line(m, "month", "quantity", "Monthly net demand • EA"))
    with business_mix:
        divisions = group_summary(data, "division")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(
                x=divisions.division,
                y=divisions.sales,
                name="Net sales (AED)",
                marker_color="#009e98",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=divisions.division,
                y=divisions.margin_pct,
                name="Gross margin %",
                mode="lines+markers",
                line_color="#173454",
            ),
            secondary_y=True,
        )
        fig.update_layout(title="Division sales and gross margin")
        fig.update_yaxes(title_text="AED", secondary_y=False)
        fig.update_yaxes(title_text="Margin %", secondary_y=True)
        l, r = st.columns(2)
        with l:
            show(fig)
        with r:
            show(
                bar(
                    group_summary(data, "product").head(10),
                    "product",
                    "sales",
                    "Top 10 products • net sales AED",
                )
            )
        l, r = st.columns(2)
        with l:
            show(
                bar(
                    group_summary(data, "category"),
                    "sales",
                    "category",
                    "Category net sales • AED",
                )
            )
        with r:
            show(
                bar(
                    group_summary(data, "channel"),
                    "channel",
                    "sales",
                    "Channel net revenue • AED",
                )
            )
    with growth_tab:
        heat = (
            data.groupby(["division", "month"])
            .quantity.sum()
            .unstack()
            .reindex(columns=sorted(months), fill_value=0)
            .fillna(0)
        )
        change = heat.copy() * np.nan
        for i in range(1, len(heat.columns)):
            if heat.columns[i] - pd.offsets.MonthBegin(1) == heat.columns[i - 1]:
                previous = heat.iloc[:, i - 1]
                change.iloc[:, i] = (
                    (heat.iloc[:, i] - previous) / previous.where(previous > 0) * 100
                )
        change.columns = [d.strftime("%b") for d in change.columns]
        if change.notna().any().any():
            fig = px.imshow(
                change,
                color_continuous_scale="RdYlGn",
                color_continuous_midpoint=0,
                aspect="auto",
                text_auto=".1f",
                title="Adjacent-month net demand growth • %",
            )
            show(fig)
        else:
            st.info(
                "Growth heatmap needs two adjacent selected months and positive prior demand."
            )
        st.subheader("Executive insights")
        insights = executive_insights(data, months)
        for i in range(0, len(insights), 2):
            columns = st.columns(2)
            for column, insight in zip(columns, insights[i : i + 2]):
                with column, st.container(border=True):
                    st.markdown(
                        '<div class="insight-label">PLANNING OBSERVATION</div>',
                        unsafe_allow_html=True,
                    )
                    st.write(insight)
        st.caption(
            "Smart alerts use explicit review thresholds, not inventory positions. Explore SKU intelligence for the drivers."
        )


def intelligence(data, months, thresholds):
    st.header("SKU & demand intelligence")
    st.caption(
        "Prioritize attention using revenue concentration and observed net-demand variability."
    )
    a, b, x, y = thresholds
    table = classify(data, months, a, b, x, y)
    st.info(
        f"ABC: positive net revenue only, A up to {a:g}%, B up to {b:g}%. Boundary-crossing SKU stays in its starting class. N = nonpositive revenue. XYZ uses {len(months)} selected calendar months; absent sales in included months are zero. CV uses population standard deviation. N = nonpositive mean. Full selection = 12-month analysis."
    )
    l, r = st.columns([2, 1])
    eligible = table.loc[table.sales > 0]
    with l:
        if len(eligible):
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Bar(
                    x=eligible["product"],
                    y=eligible.sales,
                    name="Net sales",
                    marker_color="#009e98",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=eligible["product"],
                    y=eligible.cumulative_pct,
                    name="Cumulative eligible revenue %",
                    line_color="#173454",
                ),
                secondary_y=True,
            )
            fig.update_layout(
                title="ABC revenue Pareto", xaxis={"showticklabels": False}
            )
            fig.update_yaxes(range=[0, 105], secondary_y=True)
            show(fig)
        else:
            st.info("No positive-revenue products for the Pareto chart.")
    with r:
        show(
            bar(
                table.groupby("abc").size().reset_index(name="SKUs"),
                "abc",
                "SKUs",
                "ABC distribution",
            )
        )
    matrix = pd.crosstab(table.abc, table.xyz).reindex(
        index=["A", "B", "C"], columns=["X", "Y", "Z"], fill_value=0
    )
    show(
        px.imshow(
            matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Teal",
            title="ABC–XYZ planning matrix • product counts",
        )
    )
    st.caption(
        f"Excluded from the nine-cell matrix: {((table.abc == 'N') | (table.xyz == 'N')).sum()} unclassified products."
    )
    l, r = st.columns(2)
    with l:
        segment = st.selectbox(
            "Explore planning segment", list(RECOMMENDATIONS), key="matrix_segment"
        )
        st.success(RECOMMENDATIONS[segment])
        chosen = table.loc[table.segment == segment]
        st.write(f"{len(chosen)} products · AED {chosen.sales.sum():,.2f} net sales")
        st.dataframe(
            chosen[["product", "brand", "sales", "demand_cv"]],
            hide_index=True,
            width="stretch",
        )
    with r:
        st.subheader("Smart attention signals")
        alerts = table.loc[
            table.planning_priority.str.contains(
                "Investigate|Validate|negative|nonpositive", case=False
            )
        ]
        st.write(f"{len(alerts)} products have exception signals.")
        st.dataframe(
            alerts[["product", "segment", "planning_priority"]].head(25),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Review thresholds: latest adjacent-month growth ≥20% or decline ≥20%; negative quantity rate >5%; AZ volatility; nonpositive revenue or mean. Full exception list is available in the export."
        )
    st.subheader("SKU planning workbench")
    search = st.text_input("Search product, brand or category", key="sku_search")
    visible = table
    if search:
        visible = table.loc[
            table[["product", "brand", "category"]]
            .astype(str)
            .apply(lambda s: s.str.contains(search, case=False, regex=False))
            .any(axis=1)
        ]
    st.caption(
        "Select a row to open that product's demand history below. Search narrows this table; the full segmentation export keeps your dashboard scope."
    )
    table_key = (
        "sku_workbench_"
        + hashlib.sha256(
            visible[["product", "sales"]].to_csv(index=False).encode()
        ).hexdigest()[:12]
    )
    event = st.dataframe(
        visible,
        key=table_key,
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
        width="stretch",
        column_config={
            "demand_cv": st.column_config.NumberColumn(format="%.3f"),
            "sales": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    csv_download(
        "Download ABC–XYZ & planning signals",
        table,
        "sku_segmentation.csv",
        "seg_export",
    )
    if event.selection.rows:
        row_index = event.selection.rows[0]
        token = (table_key, row_index)
        if st.session_state.get("last_sku_row") != token and row_index < len(visible):
            st.session_state["detail_product"] = visible.iloc[row_index]["product"]
            st.session_state["last_sku_row"] = token
    if st.session_state.get("detail_product") not in table["product"].tolist():
        st.session_state.pop("detail_product", None)
    sku = st.selectbox(
        "Open product demand history", table["product"].tolist(), key="detail_product"
    )
    selected = data.loc[data["product"] == sku]
    show(
        line(
            monthly_demand(selected, sorted(months)),
            "month",
            "quantity",
            f"{sku} • selected monthly net demand",
        )
    )
    st.caption(
        "Average monthly net demand = selected units / 12. selected_month_mean is the mean over included months used for CV. Monthly growth is the latest adjacent selected calendar-month comparison."
    )


def forecasting(data, months):
    st.header("Demand forecasting & scenario lab")
    st.warning(
        "Illustrative estimates, not purchase requirements. Only 12 months of scaled assessment history are available. Annual seasonality cannot be learned or validated. No inventory, lead times or service-level inputs are available."
    )
    grain = st.radio(
        "Forecast scope", ["Selected portfolio", "Category", "SKU"], horizontal=True
    )
    subset = data
    if grain != "Selected portfolio":
        col = "category" if grain == "Category" else "product"
        entity = st.selectbox(
            "Forecast entity", sorted(data[col].unique()), key="forecast_entity_" + col
        )
        subset = data.loc[data[col] == entity]
    method = st.selectbox(
        "Explainable baseline",
        ["3-month moving average", "Simple exponential smoothing"],
    )
    st.caption(
        "Try an assumption, then fine-tune the slider. These scenarios change estimates, not actual demand."
    )
    presets = st.columns(3)
    for column, label, value in zip(
        presets, ["Decline −20%", "Baseline 0%", "Growth +20%"], [-20, 0, 20]
    ):
        column.button(label, on_click=set_scenario, args=(value,), width="stretch")
    scenario = st.slider(
        "Demand scenario growth / decline (%)", -80, 100, 0, 5, key="scenario_pct"
    )
    st.caption(
        "Moving average forecasts recursively extend the last three observations. Exponential smoothing uses fixed α = 0.30 with first-observation initialization. Neither model learns annual seasonality. Signed net-demand estimates are not clipped to zero."
    )
    m = monthly_demand(subset, sorted(months))
    try:
        out, back, metrics = forecast(m, method, scenario)
    except ValueError as exc:
        st.info(str(exc))
        return
    c1, c2, c3 = st.columns(3)
    baseline_total = out.baseline.sum()
    scenario_total = out.scenario_estimate.sum()
    c1.metric("Jan–Mar baseline estimate • EA", f"{baseline_total:,.0f}", border=True)
    c2.metric(
        "Jan–Mar scenario estimate • EA",
        f"{scenario_total:,.0f}",
        delta=f"{scenario:+d}% assumption",
        delta_color="off",
        border=True,
    )
    c3.metric(
        "Estimated change • EA", f"{scenario_total - baseline_total:+,.0f}", border=True
    )
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=m.month,
            y=m.quantity,
            name="Actual 2024",
            mode="lines+markers",
            line_color="#173454",
        )
    )
    for col, label, color in [
        ("baseline", "Baseline estimate", "#009e98"),
        ("scenario_estimate", f"Scenario estimate ({scenario:+d}%)", "#e4a740"),
    ]:
        fig.add_trace(
            go.Scatter(
                x=out.month,
                y=out[col],
                name=label,
                mode="lines+markers",
                line=dict(dash="dash", color=color),
            )
        )
    fig.add_vline(
        x=pd.Timestamp("2024-12-16").timestamp() * 1000,
        line_dash="dot",
        line_color="#aab4c0",
    )
    fig.update_layout(
        title="Historical net demand and Jan–Mar 2025 estimates",
        yaxis_title="Net demand (EA)",
    )
    show(fig)
    cols = st.columns(4)
    for col, (name, value) in zip(cols, list(metrics.items())[:4]):
        col.metric(name, "N/A" if pd.isna(value) else f"{value:,.2f}", border=True)
    st.caption(
        f"Rolling one-step backtest: {metrics['Backtest periods']} held-out months, training on prior observations only. WAPE = sum |forecast−actual| / sum |actual| ×100; bias uses the same denominator, positive means overforecast. MAE is in EA. Scenario assumptions are not fitted or backtested."
    )
    st.dataframe(out, hide_index=True, width="stretch")
    csv_download(
        "Download forecast estimates",
        out.assign(
            method=method,
            scenario_pct=scenario,
            scope=grain,
            entity="Selected portfolio" if grain == "Selected portfolio" else entity,
        ),
        "forecast_estimates.csv",
        "forecast_export",
    )
    with st.expander("Compare backtests and inspect actual errors"):
        comparison = []
        for name in ["3-month moving average", "Simple exponential smoothing"]:
            _, _, result = forecast(m, name, scenario)
            comparison.append({"model": name, **result})
        st.dataframe(pd.DataFrame(comparison), hide_index=True, width="stretch")
        st.dataframe(back, hide_index=True, width="stretch")
    st.info(
        "Planner action: investigate large customer orders, promotions and returns before applying a scenario. Assess forecast uncertainty with more history; no unsupported confidence interval is shown."
    )


def assistant(data, months, thresholds, scope):
    st.header("SupplyIQ — AI Planning Assistant")
    st.caption(
        "Conversational analysis grounded in your filtered data • local read-only tools • optional LLM routing"
    )
    key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        if not key:
            key = st.secrets.get("OPENAI_API_KEY", "")
        model = st.secrets.get("OPENAI_MODEL", model)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        pass
    enabled = st.toggle(
        "Use configured LLM for question interpretation",
        value=False,
        disabled=not bool(key),
    )
    if not key:
        st.info(
            "No API key configured. The local assistant supports all example analytical questions and uses live calculations."
        )
    if enabled:
        st.caption(
            "Your question and prior intent/entity context are sent to the API. Transaction data stays local. Your question, intent context and up to 15 rows of verified aggregate results are sent to the API for interpretation. API output cannot execute queries."
        )
    history_key = hashlib.sha256((scope + str(thresholds)).encode()).hexdigest()
    if st.session_state.get("chat_scope") != history_key:
        st.session_state.chat_scope = history_key
        st.session_state.messages = []
        st.session_state.chat_context = None
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.chat_context = None
    st.caption(
        "Conversation resets when filters, workbook or classification thresholds change, preventing stale-scope answers."
    )
    example = st.selectbox(
        "Try a question",
        [
            "Which 10 SKUs generated the highest sales in 2024?",
            *FOLLOWUPS,
            "Compare demand patterns across Food and Personal Care.",
            "What was the monthly demand growth for Brand 10?",
            "Which SKUs should planners prioritize for investigation?",
            "Explain the ABC–XYZ classification of product P001.",
            "Identify significant demand anomalies.",
            "Summarize the main supply planning insights.",
            "What inventory should we replenish?",
        ],
    )
    submit = st.button("Analyze selected question")
    question = st.chat_input(
        "Ask about sales, demand, variability or planning priorities"
    )
    if submit:
        question = example
    if question:
        with st.spinner("Calculating from selected data…"):
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
        st.session_state.chat_context = result["context"]
        st.session_state.messages = st.session_state.messages[-20:]
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.write(message["text"])
            if message["role"] == "assistant":
                st.caption(message["notice"])
                table = message.get("table")
                if table is not None:
                    st.dataframe(table, hide_index=True, width="stretch")
                    csv_download(
                        "Download verified result",
                        table,
                        "supplyiq_result.csv",
                        f"chat_csv_{i}",
                    )
                    chart = message.get("chart")
                    if chart and not table.empty:
                        kind, x, y = chart
                        fig = (
                            line(
                                table,
                                x,
                                y,
                                "Verified analytical result",
                                "division" if kind == "comparison" else None,
                            )
                            if kind in ["line", "comparison"]
                            else bar(table, x, y, "Verified analytical result")
                        )
                        show(fig, key=f"chat_chart_{i}")
                st.caption("Follow up: " + " • ".join(FOLLOWUPS))
    st.caption(
        "No free-form SQL or code execution. Questions are mapped to fixed analytical functions; DuckDB runs parameterized, fixed read-only aggregation. API failure falls back to the local assistant. Forecasts and classification are analytical estimates, not inventory advice."
    )


def quality(data, report, filtered, months):
    st.header("Data quality & reconciliation")
    st.success(
        "Sales-to-master joins preserve row count and financial totals."
        if report["reconciled"]
        else "Reconciliation needs review."
    )
    st.caption(
        "Quality results below describe the entire uploaded workbook. The filtered extract and metrics are explicitly separated."
    )
    l, r = st.columns(2)
    with l:
        st.subheader("Workbook validation")
        rows = [
            {"Check": k.replace("_", " ").title(), "Result": str(v)}
            for k, v in report.items()
            if k not in ["about"]
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    with r:
        st.subheader("Source business context")
        if report["sign_mismatch_rows"]:
            st.warning(
                f"{report['sign_mismatch_rows']} rows have opposite signs between quantity and sales or cost. Values are preserved; validate these credits/cost adjustments with the source owner."
            )
        st.write(report["about"])
        st.info(
            "Negative values are retained as returns/credits. Exact duplicate rows are reported, never silently deleted. Master conflicts, unknown keys, invalid numerics/dates or mixed UOM block ingestion rather than produce misleading metrics."
        )
        st.subheader("Filtered scope")
        st.write(
            f"{len(filtered):,} rows · {len(months)} selected months · {filtered['product'].nunique()} products"
        )
        st.dataframe(pd.DataFrame([kpis(filtered, months)]), hide_index=True)
    st.subheader("Positive sales versus negative transactions • filtered scope")
    breakdown = pd.DataFrame(
        [
            {
                "measure": c,
                "positive_total": filtered[c].clip(lower=0).sum(),
                "negative_total": filtered[c].clip(upper=0).sum(),
                "net_total": filtered[c].sum(),
            }
            for c in ["quantity", "sales", "cost"]
        ]
    )
    st.dataframe(breakdown, hide_index=True, width="stretch")
    csv_download(
        "Download filtered transactions",
        filtered,
        "filtered_sales.csv",
        "filtered_export",
    )
    csv_download(
        "Download validation report",
        pd.DataFrame(rows),
        "data_quality.csv",
        "quality_export",
    )
