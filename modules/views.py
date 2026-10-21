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
from .usability import set_scenario, navigate
from .assistant_actions import queue_question
from .presentation import display_table
from .visualizations import show, line, bar

DEFINITIONS = {
    "Net Sales (AED)": "Sales after returns and credit notes have been deducted.",
    "Net Units Sold": "Units sold minus units returned. EA means individual units; pack sizes may differ between products.",
    "Gross Profit (AED)": "Sales after returns, minus the cost of those sales.",
    "Gross Margin %": "The share of sales left after product costs: gross profit ÷ net sales × 100. N/A means it cannot be calculated because sales are zero. Treat percentages based on negative sales with care.",
    "MoM Demand Growth %": "How much units sold changed from the previous month. Both months must be selected, and the previous month must have more than zero units.",
    "Active SKUs": "Number of different products with a sale or return in your selection. SKU means a product code.",
    "Average Monthly Net Demand": "Units sold minus returns, divided by 12. If you select fewer months, this still divides by 12; it is not the average of just those months.",
    "Negative Transaction Quantity Rate %": "Returned or credited units as a percentage of positive units sold. N/A means there are no positive units to compare with. This is a share of units, not a share of transaction rows.",
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
    """One dashboard canvas; secondary analysis stays below the main view."""
    st.header("Executive overview")
    metrics = kpis(data, months)
    m = monthly_demand(data, sorted(months))
    for offset in (0, 4):
        columns = st.columns(4)
        for i, (column, (name, value)) in enumerate(
            zip(columns, list(metrics.items())[offset : offset + 4]), start=offset
        ):
            with column, st.container(border=True, key=f"kpi_card_{i}"):
                text = (
                    "N/A"
                    if pd.isna(value)
                    else f"{value:,.2f}%"
                    if "%" in name
                    else f"{value:,.0f}"
                )
                st.metric(name, text, help=DEFINITIONS[name])
    trend, divisions_panel = st.columns([1.4, 1])
    with trend, st.container(border=True, key="dashboard_trend"):
        st.subheader("Monthly performance")
        measure = st.segmented_control(
            "View",
            ["Net Sales", "Net Units"],
            default="Net Sales",
            key="dashboard_measure",
        )
        field = "quantity" if measure == "Net Units" else "sales"
        title = (
            "Monthly net demand • EA"
            if field == "quantity"
            else "Monthly net sales • AED"
        )
        fig = px.area(
            m,
            x="month",
            y=field,
            markers=True,
            title=title,
            labels={
                "month": "Month",
                "sales": "Net sales (AED)",
                "quantity": "Net demand (EA)",
            },
        )
        fig.update_traces(line_color="#009e98", fillcolor="rgba(0,158,152,.10)")
        fig.update_layout(height=300)
        show(fig, key="dashboard_monthly")
    with divisions_panel, st.container(border=True, key="dashboard_divisions"):
        st.subheader("Division performance")
        divisions = group_summary(data, "division")
        division_measure = st.segmented_control(
            "Division measure",
            ["Net Sales", "Gross Margin"],
            default="Net Sales",
            key="dashboard_division_measure",
        )
        field = "margin_pct" if division_measure == "Gross Margin" else "sales"
        fig = bar(
            divisions,
            field,
            "division",
            "Division gross margin • %"
            if field == "margin_pct"
            else "Division net sales • AED",
        )
        fig.update_traces(
            customdata=divisions[["sales", "margin_pct"]].to_numpy(),
            hovertemplate="Division: %{y}<br>Net sales: AED %{customdata[0]:,.2f}<br>Gross margin: %{customdata[1]:.2f}%<extra></extra>",
        )
        fig.update_layout(height=300, yaxis={"categoryorder": "total ascending"})
        if field == "margin_pct":
            fig.update_xaxes(title_text="Gross margin (%)")
        show(
            fig,
            key="dashboard_divisions_chart",
            help_text="Choose Net Sales or Gross Margin to compare divisions. Hover to see both sales in AED and gross margin. Returns and credit notes are included. These figures follow your sidebar filters.",
        )

    products, alerts = st.columns([1.4, 1])
    with products, st.container(border=True, key="dashboard_products"):
        st.subheader("Top 10 SKUs")
        top = group_summary(data, "product").head(10).sort_values("sales")
        fig = bar(top, "sales", "product", "Top 10 products • net sales AED")
        fig.update_layout(height=340)
        show(fig, key="dashboard_top_products")
    with alerts, st.container(border=True, key="dashboard_alerts"):
        st.subheader("Planning attention")
        insights = executive_insights(data, months)
        for i in [2, 3, 0]:
            if i < len(insights):
                st.write(insights[i])
        st.caption(
            "Demand review signals only. Stock availability is not included in this workbook."
        )
        st.button(
            "Review priority SKUs",
            key="dashboard_review_skus",
            on_click=navigate,
            args=("SKU analysis",),
            width="stretch",
        )
    with st.expander("More breakdowns: categories, channels & monthly changes"):
        left, right = st.columns(2)
        with left:
            show(
                bar(
                    group_summary(data, "category"),
                    "sales",
                    "category",
                    "Category net sales • AED",
                )
            )
        with right:
            show(
                bar(
                    group_summary(data, "channel"),
                    "channel",
                    "sales",
                    "Channel net revenue • AED",
                )
            )
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
            show(
                px.imshow(
                    change,
                    color_continuous_scale="RdYlGn",
                    color_continuous_midpoint=0,
                    aspect="auto",
                    text_auto=".1f",
                    title="Adjacent-month net demand growth • %",
                )
            )
        else:
            st.info(
                "Growth heatmap needs two adjacent selected months and positive prior demand."
            )
        st.subheader("Executive insights")
        for insight in insights:
            st.write(insight)
    with st.expander("Explore an individual KPI trend"):
        focused = st.selectbox("KPI", list(metrics), key="dashboard_detail_metric")
        history = pd.DataFrame(
            [kpis(data.loc[data.month == month], [month]) for month in m.month]
        )
        history["month"] = m.month.to_numpy()
        history["MoM Demand Growth %"] = m.growth_pct.to_numpy()
        for i in range(1, len(m)):
            if m.month.iloc[i] - pd.offsets.MonthBegin(1) != m.month.iloc[i - 1]:
                history.loc[i, "MoM Demand Growth %"] = np.nan
        show(
            line(history, "month", focused, "Selected KPI • monthly history"),
            key="dashboard_detail_chart",
            help_text=DEFINITIONS[focused]
            + " Each point shows the measure for that selected month. The KPI cards summarize the whole selection.",
        )


def intelligence(data, months, thresholds):
    st.header("SKU analysis")
    st.caption(
        "Find important products and see how much their sales quantities change each month."
    )
    a, b, x, y = thresholds
    table = classify(data, months, a, b, x, y)
    with st.expander("How ABC–XYZ groups work"):
        st.info(
            f"ABC groups products by sales value: A covers roughly the first {a:g}% of positive sales, B continues up to {b:g}%, and C covers the rest. A product that crosses a cutoff stays in the group where it started. XYZ shows how steady demand is: X = steady, Y = some changes, Z = large changes. We use your {len(months)} selected months and count months with no sales as zero. N means sales or average demand is zero or less, so that product cannot join the usual groups."
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
        display_table(
            chosen[["product", "brand", "sales", "demand_cv"]],
            hide_index=True,
            width="stretch",
        )
    with r:
        st.subheader("Planning alerts")
        alerts = table.loc[
            table.planning_priority.str.contains(
                "Investigate|Validate|negative|nonpositive", case=False
            )
        ]
        st.write(f"{len(alerts)} products have exception signals.")
        display_table(
            alerts[["product", "segment", "planning_priority"]].head(25),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "We flag monthly rises or falls of at least 20%, returned/credited units above 5%, important products with uneven demand (AZ), and sales or average units of zero or less. Download the full list for review."
        )
    st.subheader("SKU explorer")
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
        "Select a row to see that product’s monthly demand below. Search only changes this table; the download still includes every product matching your sidebar filters."
    )
    table_key = (
        "sku_workbench_"
        + hashlib.sha256(
            visible[["product", "sales"]].to_csv(index=False).encode()
        ).hexdigest()[:12]
    )
    event = display_table(
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
        "Average monthly net demand always divides selected units by 12. Average in selected months uses only the months you chose and is used to measure demand consistency. Monthly growth compares the latest month with the previous month, when both are selected."
    )


def forecasting(data, months):
    st.header("Demand forecasting")
    st.warning(
        "These forecasts are examples, not quantities to order. We have only one year of adjusted assessment data, so we cannot confirm patterns that repeat each year. Current stock, supplier delivery times and customer service targets are not provided."
    )
    grain = st.radio(
        "Forecast scope",
        ["Selected portfolio", "Category", "SKU"],
        horizontal=True,
    )
    subset = data
    if grain != "Selected portfolio":
        col = "category" if grain == "Category" else "product"
        entity = st.selectbox(
            "Select category or SKU",
            sorted(data[col].unique()),
            key="forecast_entity_" + col,
        )
        subset = data.loc[data[col] == entity]
    method = st.selectbox(
        "Forecast method",
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
        "The 3-month average uses the latest three values; later estimates also use earlier forecast values. Exponential smoothing gives more weight to recent months (30% to the latest month, 70% to the earlier estimate). Neither method learns yearly patterns. Estimates keep returns included and may be negative."
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
        "Estimated change • EA",
        f"{scenario_total - baseline_total:+,.0f}",
        border=True,
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
        help_text = {
            "MAE": "The average size of the gap between forecast and actual units. Smaller is better.",
            "WAPE %": "Total absolute error divided by total absolute actual units, as a percentage. Smaller is better. N/A means actual units add up to zero after taking absolute values.",
            "Bias %": "Positive means estimates tend to be too high; negative means too low. Error is compared with total absolute actual units.",
            "Mean bias (units)": "Average forecast minus actual units. Positive means too high; negative means too low.",
        }
        col.metric(
            name,
            "N/A" if pd.isna(value) else f"{value:,.2f}",
            border=True,
            help=help_text.get(name),
        )
    st.caption(
        f"We tested the method on {metrics['Backtest periods']} past months, predicting each month using only earlier data. MAE is the average size of the error in units. WAPE is total absolute error ÷ total absolute actual units × 100. Bias uses the same total to show whether estimates are too high (+) or too low (−). Your growth/decline assumption is not part of this test."
    )
    display_table(out, hide_index=True, width="stretch")
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
        display_table(pd.DataFrame(comparison), hide_index=True, width="stretch")
        display_table(back, hide_index=True, width="stretch")
    st.info(
        "Planner action: investigate large customer orders, promotions and returns before applying a scenario. Assess forecast uncertainty with more history; no unsupported confidence interval is shown."
    )


def assistant(data, months, thresholds, scope):
    st.header("SupplyIQ — AI Planning Assistant")
    st.caption(
        "Ask questions about your selected data. Answers use calculated results."
    )
    key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        if not key:
            key = st.secrets.get("OPENAI_API_KEY", "")
        model = st.secrets.get("OPENAI_MODEL", model)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        pass
    st.success("Ready to help with your selected sales data.", icon=":material/chat:")
    with st.expander("Optional AI settings"):
        enabled = st.toggle(
            "Use configured LLM for question interpretation",
            value=False,
            disabled=not bool(key),
        )
        if not key:
            st.info(
                "The built-in assistant is ready to use without an API key. Try one of the questions below."
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
        "Chat starts fresh when you change filters, the file or group settings, so old answers are not mixed with new selections."
    )
    st.subheader("What would you like to know?")
    st.caption(
        "Choose a button to get an answer from your selected data, or type your own question below."
    )
    quick_questions = [
        ("Summarize my data", "Summarize the main supply planning insights."),
        ("Top 10 SKUs", "Which 10 SKUs generated the highest sales in 2024?"),
        ("Demand variability", "Which products have the biggest demand swings?"),
        ("Show AZ products", "Which products belong to the AZ category?"),
        ("Declining categories", "Which categories experienced declining demand?"),
        ("Unusual demand changes", "Identify significant demand anomalies."),
    ]
    for offset in (0, 3):
        columns = st.columns(3)
        for column, (label, prompt) in zip(
            columns, quick_questions[offset : offset + 3]
        ):
            column.button(
                label,
                key="quick_" + str(offset) + "_" + label,
                on_click=queue_question,
                args=(prompt,),
                width="stretch",
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
    queued = st.session_state.pop("assistant_pending_question", None)
    if not question and queued:
        question = queued
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
                    display_table(table, hide_index=True, width="stretch")
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
                                "Results from your data",
                                "division" if kind == "comparison" else None,
                            )
                            if kind in ["line", "comparison"]
                            else bar(table, x, y, "Results from your data")
                        )
                        show(fig, key=f"chat_chart_{i}")
                st.caption("Follow up: " + " • ".join(FOLLOWUPS))
    if st.session_state.messages:
        st.markdown("**Keep exploring**")
        followups = st.columns(3)
        for i, (column, label, prompt) in enumerate(
            zip(
                followups,
                ["Review priorities", "Monthly demand", "Explain missing stock data"],
                [
                    "Which SKUs should planners prioritize for investigation?",
                    "Show monthly demand growth",
                    "What inventory should we replenish?",
                ],
            )
        ):
            column.button(
                label,
                key=f"followup_{i}",
                on_click=queue_question,
                args=(prompt,),
                width="stretch",
            )
    with st.expander("How SupplyIQ answers questions"):
        st.write(
            "SupplyIQ calculates answers from the sales data matching your filters. It uses a fixed set of safe calculations. The optional AI service helps understand questions and explain results. If that service is unavailable, built-in analysis still works. Stock levels, supplier delivery times and order requirements are not available in this file."
        )


def quality(data, report, filtered, months):
    st.header("Data quality & totals")
    st.success(
        "Sales records match the product and customer lists. Row counts and totals are unchanged."
        if report["reconciled"]
        else "Some totals do not match and need checking."
    )
    st.caption(
        "Workbook validation cover the whole workbook. Your filtered results are shown separately."
    )
    l, r = st.columns(2)
    with l:
        st.subheader("Workbook validation")
        rows = [
            {"Check": k.replace("_", " ").title(), "Result": str(v)}
            for k, v in report.items()
            if k not in ["about"]
        ]
        display_table(pd.DataFrame(rows), hide_index=True, width="stretch")
    with r:
        st.subheader("Source business context")
        if report["sign_mismatch_rows"]:
            st.warning(
                f"{report['sign_mismatch_rows']} rows have opposite signs between quantity and sales or cost. Values are preserved; check these credit or cost adjustments with the person who provided the data."
            )
        st.write(report["about"])
        st.info(
            "Negative values are kept as returns or credit notes. Repeated rows are reported, not deleted. If product or customer details do not match, dates or numbers are invalid, or units of measure differ, the app stops and asks for the file to be corrected."
        )
        st.subheader("Filtered scope")
        st.write(
            f"{len(filtered):,} rows · {len(months)} selected months · {filtered['product'].nunique()} products"
        )
        display_table(pd.DataFrame([kpis(filtered, months)]), hide_index=True)
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
    display_table(breakdown, hide_index=True, width="stretch")
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
