import hashlib
from html import escape
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from .kpi_calculations import kpis, monthly_demand, group_summary, executive_insights
from .abc_xyz_analysis import classify, RECOMMENDATIONS
from .forecasting import forecast
from .usability import set_scenario, navigate
from .presentation import display_table
from .visualizations import show, line, bar
from .palette import NAVY, NAVY_BAR, GOLD, GOLD_LIGHT, SLATE, SEQUENTIAL, DIVERGING

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


def overview(
    data,
    months,
    reference_data=None,
    thresholds=(80, 95, 0.5, 1),
    scope="",
    available_months=None,
):
    """Four headline metrics, one main trend, an action rail, then comparisons."""
    from .period_comparison import compare_period
    from .reporting import planning_brief

    title, tools = st.columns([4, 1], vertical_alignment="center")
    title.header("Executive overview")
    with tools.popover("Review tools", icon=":material/tune:", width="stretch"):
        compare = st.toggle(
            "Compare with previous period", key="overview_compare", value=False
        )
        st.caption(
            "Equal-length, consecutive periods using the same product/customer filters. Previous data must be within 2024."
        )
        if st.button("Prepare planning brief", key="prepare_brief", width="stretch"):
            with st.spinner("Preparing your selected-data brief…"):
                st.session_state["prepared_brief"] = (
                    scope + str(thresholds),
                    planning_brief(data, months, thresholds),
                )
        prepared = st.session_state.get("prepared_brief")
        if prepared and prepared[0] == scope + str(thresholds):
            st.download_button(
                "Download planning brief",
                prepared[1],
                file_name="supplyiq_planning_brief.zip",
                mime="application/zip",
                key="planning_brief_export",
                width="stretch",
            )
            st.caption(
                "Contains a readable summary, KPI totals, monthly trends, segmentation and filter metadata. No external publishing."
            )
    comparison = (
        compare_period(
            reference_data if reference_data is not None else data,
            months,
            available_months,
        )
        if compare
        else None
    )
    if comparison and not comparison["available"]:
        st.caption("Previous-period comparison: " + comparison["reason"])
    metrics = kpis(data, months)
    m = monthly_demand(data, sorted(months))
    for i, (column, (name, value)) in enumerate(
        zip(st.columns(4), list(metrics.items())[:4])
    ):
        with column, st.container(border=True, key=f"kpi_card_{i}"):
            st.markdown(
                '<div class="metric-kicker">'
                + ["Revenue", "Volume", "Profit", "Margin"][i]
                + "</div>",
                unsafe_allow_html=True,
            )
            text = (
                "N/A"
                if pd.isna(value)
                else f"{value:,.2f}%"
                if "%" in name
                else f"{value:,.0f}"
            )
            delta = None
            if (
                comparison
                and comparison["available"]
                and pd.notna(comparison["deltas"][name])
            ):
                suffix = "pp" if name == "Gross Margin %" else "%"
                delta = f"{comparison['deltas'][name]:+.1f}{suffix} vs {comparison['label']}"
            st.metric(
                name, text, delta=delta, delta_color="off", help=DEFINITIONS[name]
            )
    trend, attention = st.columns([2.05, 1])
    divisions = group_summary(data, "division")
    insights = executive_insights(data, months)
    with trend, st.container(border=True, key="dashboard_trend"):
        title_slot, view_slot = st.columns([3, 2], vertical_alignment="center")
        title_slot.subheader("Monthly performance")
        with view_slot:
            measure = st.segmented_control(
                "View",
                ["Net Sales", "Net Units"],
                default="Net Sales",
                key="dashboard_measure",
                label_visibility="collapsed",
            )
        field = "quantity" if measure == "Net Units" else "sales"
        fig = px.area(
            m,
            x="month",
            y=field,
            markers=True,
            labels={
                "month": "Month",
                "sales": "Net sales (AED)",
                "quantity": "Net demand (EA)",
            },
        )
        fig.update_traces(
            line=dict(color=NAVY, width=3),
            marker=dict(size=6, color=GOLD_LIGHT, line=dict(color=NAVY, width=2)),
            fillcolor="rgba(185,145,70,.10)",
        )
        fig.update_layout(height=310)
        fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
        description = (
            "Each point shows sales after returns in AED for a selected month."
            if field == "sales"
            else "Each point shows units sold minus returns for a selected month. EA means individual units; pack sizes can differ."
        )
        show(
            fig,
            key="dashboard_monthly",
            help_text=description
            + " Hover for exact values. All results follow the top filter bar.",
        )
    with attention, st.container(border=True, key="dashboard_alerts"):
        st.subheader("Planning attention")
        growth_value = metrics["MoM Demand Growth %"]
        rate = metrics["Negative Transaction Quantity Rate %"]
        latest = sorted(months)
        cards = []
        if pd.notna(growth_value):
            cards.append(
                (
                    "LATEST DEMAND CHANGE",
                    f"{growth_value:+.2f}%",
                    f"{latest[-1]:%b} versus {latest[-2]:%b}. Check the customer and product changes behind this movement.",
                )
            )
        else:
            cards.append(
                (
                    "LATEST DEMAND CHANGE",
                    "N/A",
                    "Select neighbouring months with positive demand in the earlier month to compare them.",
                )
            )
        if len(divisions):
            leader = divisions.iloc[0]
            share = (
                leader.sales / data.sales.sum() * 100
                if data.sales.sum() > 0
                else float("nan")
            )
            value = f"{share:.1f}%" if pd.notna(share) else "N/A"
            cards.append(
                (
                    "LEADING DIVISION",
                    value,
                    f"{leader.division} share of selected net sales.",
                )
            )
        cards.append(
            (
                "NEGATIVE QUANTITY RATE",
                f"{rate:.2f}%" if pd.notna(rate) else "N/A",
                "Returned or credited units compared with positive units sold.",
            )
        )
        for label, value, detail in cards:
            st.markdown(
                '<div class="attention-item"><span class="attention-index">'
                + label
                + '</span><strong class="attention-value">'
                + escape(value)
                + "</strong><p>"
                + escape(detail)
                + "</p></div>",
                unsafe_allow_html=True,
            )
        st.button(
            "Review priority SKUs",
            key="dashboard_review_skus",
            on_click=navigate,
            args=("SKU analysis",),
            width="stretch",
        )
        st.caption("Sales signals only · no stock data.")
    divisions_panel, products = st.columns(2)
    with divisions_panel, st.container(border=True, key="dashboard_divisions"):
        st.subheader("Division performance")
        measure = st.segmented_control(
            "Division measure",
            ["Net Sales", "Gross Margin"],
            default="Net Sales",
            key="dashboard_division_measure",
            label_visibility="collapsed",
        )
        field = "margin_pct" if measure == "Gross Margin" else "sales"
        fig = bar(divisions, field, "division", "")
        fig.update_traces(
            marker_color=[
                GOLD if pd.notna(v) and v == divisions[field].max() else NAVY_BAR
                for v in divisions[field]
            ],
            customdata=[
                [
                    row.sales,
                    f"{row.margin_pct:.2f}%" if pd.notna(row.margin_pct) else "N/A",
                ]
                for _, row in divisions.iterrows()
            ],
            hovertemplate="Division: %{y}<br>Net sales: AED %{customdata[0]:,.2f}<br>Gross margin: %{customdata[1]}<extra></extra>",
        )
        fig.update_layout(height=300, yaxis={"categoryorder": "total ascending"})
        fig.update_xaxes(
            title_text="Gross margin (%)"
            if field == "margin_pct"
            else "Net sales (AED)"
        )
        show(
            fig,
            key="dashboard_divisions_chart",
            help_text="Compare divisions by Net Sales or Gross Margin. Hover to see both measures. All figures follow the selected filters; N/A means margin cannot be calculated.",
        )
    with products, st.container(border=True, key="dashboard_products"):
        st.subheader("Top 10 SKUs")
        top = group_summary(data, "product").head(10).sort_values("sales")
        fig = bar(top, "sales", "product", "")
        fig.update_traces(
            marker_color=[
                GOLD if sku == top.iloc[-1]["product"] else NAVY_BAR
                for sku in top["product"]
            ]
        )
        fig.update_layout(height=334)
        show(
            fig,
            key="dashboard_top_products",
            help_text="Products ranked by net sales in AED, after returns and credit notes. Longer bars mean more sales value. These are not stock levels.",
        )
    with st.expander("Additional KPIs: demand growth, active SKUs & returns"):
        for i, (column, (name, value)) in enumerate(
            zip(st.columns(4), list(metrics.items())[4:]), start=4
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
                    color_continuous_scale=DIVERGING,
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

    def reset_explorer():
        for key, value in {
            "sku_search": "",
            "workbench_abc": [],
            "workbench_xyz": [],
            "workbench_focus": "All products",
            "workbench_sort": "Net sales ↓",
        }.items():
            st.session_state[key] = value
        st.session_state.pop("detail_product", None)
        st.session_state.pop("last_sku_row", None)

    def explore_segment(value):
        reset_explorer()
        st.session_state["workbench_abc"] = [value[0]]
        st.session_state["workbench_xyz"] = [value[1]]

    exception_mask = (
        (table["segment"] == "AZ")
        | table["monthly_demand_growth_pct"].abs().ge(20)
        | table["negative_quantity_rate_pct"].gt(5)
        | table["abc"].eq("N")
        | table["xyz"].eq("N")
    )
    eligible_revenue = table["sales"].clip(lower=0).sum()
    a_share = (
        table.loc[table["abc"].eq("A"), "sales"].sum() / eligible_revenue * 100
        if eligible_revenue > 0
        else np.nan
    )
    summary = st.columns(4)
    summary[0].metric("SKUs in selection", f"{len(table):,}", border=True)
    summary[1].metric(
        "High-value volatile SKUs (AZ)",
        f"{table['segment'].eq('AZ').sum():,}",
        border=True,
    )
    summary[2].metric(
        "A share of eligible revenue",
        "N/A" if pd.isna(a_share) else f"{a_share:.1f}%",
        border=True,
        help="Share of positive net SKU revenue assigned to class A. Boundary-crossing products can take the share beyond the chosen cutoff.",
    )
    summary[3].metric(
        "SKUs with exception signals",
        f"{exception_mask.sum():,}",
        border=True,
        help="AZ products, latest adjacent-month changes of at least 20%, negative quantity rate above 5%, or unclassified revenue/demand. These are review signals, not order instructions.",
    )
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
                    marker_color=NAVY_BAR,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=eligible["product"],
                    y=eligible.cumulative_pct,
                    name="Cumulative eligible revenue %",
                    line_color=NAVY,
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
            color_continuous_scale=SEQUENTIAL,
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
        st.button(
            "Use this segment in explorer",
            key="apply_workbench_segment",
            on_click=explore_segment,
            args=(segment,),
            width="stretch",
        )
        chosen = table.loc[table.segment == segment]
        st.write(f"{len(chosen)} products · AED {chosen.sales.sum():,.2f} net sales")
        display_table(
            chosen[["product", "brand", "sales", "demand_cv"]],
            hide_index=True,
            width="stretch",
        )
    with r:
        st.subheader("Planning alerts")
        alerts = table.loc[exception_mask]
        st.write(f"{len(alerts)} products have exception signals.")
        display_table(
            alerts[["product", "segment", "planning_priority"]].head(25),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "We flag monthly rises or falls of at least 20%, returned/credited units above 5%, important products with uneven demand (AZ), and sales or average units of zero or less. Download the full list for review."
        )
    heading, reset = st.columns([4, 1], vertical_alignment="center")
    heading.subheader("SKU explorer")
    reset.button(
        "Reset explorer",
        key="workbench_reset",
        on_click=reset_explorer,
        width="stretch",
    )
    search = st.text_input(
        "Search product, brand or category",
        key="sku_search",
        placeholder="For example: P001 or Brand 10",
    )
    abc_control, xyz_control, focus_control, sort_control = st.columns([1, 1, 2, 1.5])
    abc_classes = abc_control.multiselect(
        "ABC class",
        ["A", "B", "C", "N"],
        key="workbench_abc",
        placeholder="All classes",
    )
    xyz_classes = xyz_control.multiselect(
        "XYZ class",
        ["X", "Y", "Z", "N"],
        key="workbench_xyz",
        placeholder="All classes",
    )
    focus = focus_control.selectbox(
        "Planning focus",
        [
            "All products",
            "Exception signals",
            "High-value volatile (AZ)",
            "High-value steady (AX)",
            "Demand drop ≥20%",
            "Demand rise ≥20%",
            "Negative quantity rate >5%",
            "Low contribution (C)",
            "Unclassified (N)",
        ],
        key="workbench_focus",
    )
    ordering = sort_control.selectbox(
        "Sort products by",
        [
            "Net sales ↓",
            "Demand CV ↓",
            "Demand growth ↓",
            "Demand growth ↑",
            "Negative quantity rate ↓",
            "Product code ↑",
        ],
        key="workbench_sort",
    )
    mask = pd.Series(True, index=table.index)
    if search:
        mask &= (
            table[["product", "brand", "category"]]
            .astype(str)
            .apply(lambda values: values.str.contains(search, case=False, regex=False))
            .any(axis=1)
        )
    if abc_classes:
        mask &= table["abc"].isin(abc_classes)
    if xyz_classes:
        mask &= table["xyz"].isin(xyz_classes)
    focus_masks = {
        "Exception signals": exception_mask,
        "High-value volatile (AZ)": table["segment"].eq("AZ"),
        "High-value steady (AX)": table["segment"].eq("AX"),
        "Demand drop ≥20%": table["monthly_demand_growth_pct"].le(-20),
        "Demand rise ≥20%": table["monthly_demand_growth_pct"].ge(20),
        "Negative quantity rate >5%": table["negative_quantity_rate_pct"].gt(5),
        "Low contribution (C)": table["abc"].eq("C"),
        "Unclassified (N)": table["abc"].eq("N") | table["xyz"].eq("N"),
    }
    if focus in focus_masks:
        mask &= focus_masks[focus]
    sort_column, ascending = {
        "Net sales ↓": ("sales", False),
        "Demand CV ↓": ("demand_cv", False),
        "Demand growth ↓": ("monthly_demand_growth_pct", False),
        "Demand growth ↑": ("monthly_demand_growth_pct", True),
        "Negative quantity rate ↓": ("negative_quantity_rate_pct", False),
        "Product code ↑": ("product", True),
    }[ordering]
    sort_fields = (
        [sort_column] if sort_column == "product" else [sort_column, "product"]
    )
    visible = (
        table.loc[mask]
        .sort_values(
            sort_fields,
            ascending=[ascending] if len(sort_fields) == 1 else [ascending, True],
            na_position="last",
        )
        .copy()
    )
    st.caption(
        f"Showing {len(visible):,} of {len(table):,} SKUs. Explorer controls combine; classification stays relative to the dashboard filters, not this smaller view."
    )
    if visible.empty:
        st.info(
            "No SKUs match these explorer controls. Reset the explorer or choose a broader class/focus."
        )
    else:
        st.caption(
            "Select a row to open that product’s demand history below. A review signal is a reason to investigate, not a replenishment instruction."
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
        column_order=[
            "product",
            "abc",
            "xyz",
            "sales",
            "quantity",
            "demand_cv",
            "monthly_demand_growth_pct",
            "planning_priority",
            "brand",
            "division",
            "category",
            "average_monthly_demand",
            "gross_margin_pct",
            "negative_quantity_rate_pct",
        ],
        column_config={
            "demand_cv": st.column_config.NumberColumn(
                format="%.3f",
                help="How much monthly demand changes relative to its positive average. Lower values mean steadier demand.",
            ),
            "sales": st.column_config.NumberColumn(
                format="%.2f", help="Net sales after returns and credits, in AED."
            ),
        },
    )
    selected_export, full_export = st.columns(2)
    with selected_export:
        st.download_button(
            "Download explorer view",
            visible.to_csv(index=False).encode("utf-8-sig"),
            file_name="sku_workbench.csv",
            mime="text/csv",
            key="workbench_export",
            disabled=visible.empty,
        )
    with full_export:
        csv_download(
            "Download ABC–XYZ & planning signals",
            table,
            "sku_segmentation.csv",
            "seg_export",
        )
    if visible.empty:
        st.session_state.pop("detail_product", None)
        st.session_state.pop("last_sku_row", None)
        return
    if event.selection.rows:
        row_index = event.selection.rows[0]
        token = (table_key, row_index)
        if st.session_state.get("last_sku_row") != token and row_index < len(visible):
            st.session_state["detail_product"] = visible.iloc[row_index]["product"]
            st.session_state["last_sku_row"] = token
    products = visible["product"].tolist()
    if st.session_state.get("detail_product") not in products:
        st.session_state.pop("detail_product", None)
    sku = st.selectbox("Open product demand history", products, key="detail_product")
    chosen_sku = visible.loc[visible["product"].eq(sku)].iloc[0]
    st.caption(
        f"{sku} · {chosen_sku['brand']} · {chosen_sku['category']} · ABC–XYZ: {chosen_sku['segment']}"
    )
    st.info(
        RECOMMENDATIONS.get(
            chosen_sku["segment"],
            "Review sales and returns: revenue or average demand is zero or less, so the standard matrix does not apply.",
        )
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
    from .forecasting import compare_models, forecast_review_bundle

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
    entity = "Selected portfolio"
    if grain != "Selected portfolio":
        col = "category" if grain == "Category" else "product"
        options = sorted(data[col].unique())
        entity_key = "forecast_entity_" + col
        if st.session_state.get(entity_key) not in options:
            st.session_state.pop(entity_key, None)
        entity = st.selectbox(
            "Select category or SKU",
            options,
            key=entity_key,
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
        comparison, paths = compare_models(m)
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
            line_color=NAVY,
        )
    )
    for col, label, color in [
        ("baseline", "Baseline estimate", GOLD),
        ("scenario_estimate", f"Scenario estimate ({scenario:+d}%)", SLATE),
    ]:
        if col == "scenario_estimate" and scenario == 0:
            continue
        fig.add_trace(
            go.Scatter(
                x=out.month,
                y=out[col],
                name=label,
                mode="lines+markers",
                line=dict(dash="dash" if col == "baseline" else "dot", color=color),
            )
        )
    fig.add_vline(
        x=pd.Timestamp("2024-12-16").timestamp() * 1000,
        line_dash="dot",
        line_color="#aab4c0",
    )
    fig.add_vrect(
        x0=pd.Timestamp("2025-01-01").timestamp() * 1000,
        x1=pd.Timestamp("2025-03-15").timestamp() * 1000,
        fillcolor="rgba(185,145,70,.07)",
        line_width=0,
        layer="below",
    )
    fig.update_layout(
        title="Historical net demand and Jan–Mar 2025 estimates",
        yaxis_title="Net demand (EA)",
    )
    show(fig)
    st.caption(
        "The shaded area contains estimates for January–March 2025. Solid navy is observed 2024 demand; "
        "gold dashes are the baseline. A dotted scenario line appears when the assumption differs from 0%."
    )
    st.subheader("How dependable is this starting point?")
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
    estimate_export = out.assign(
        method=method,
        scenario_pct=scenario,
        scope=grain,
        entity=entity,
        quantity_type="signed_net_demand",
        unit="EA",
        history_start=m.month.min().strftime("%Y-%m-%d"),
        history_end=m.month.max().strftime("%Y-%m-%d"),
        observation_months=len(m),
        status="illustrative_estimate_not_purchase_requirement",
    )
    csv_download(
        "Download forecast estimates",
        estimate_export,
        "forecast_estimates.csv",
        "forecast_export",
    )
    one_step = comparison.loc[comparison.horizon_months == 1]
    best = one_step.sort_values(["MAE", "model"]).iloc[0]
    if one_step["MAE"].nunique() == 1:
        st.info(
            "Both methods have the same one-month historical MAE in this selection. This does not guarantee equal future performance."
        )
    else:
        st.info(
            f"{best['model']} has the lower one-month historical MAE ({best['MAE']:,.2f} EA) "
            f"across the same {int(best['test_origins'])} test months. This is a comparison within this selection, "
            "not a guarantee of future accuracy or a recommendation to place orders."
        )
    with st.expander("Compare methods and inspect forecast errors"):
        st.markdown("**One-month predictions — same test months for both methods**")
        display_table(
            one_step.drop(columns=["horizon_months"]), hide_index=True, width="stretch"
        )
        st.markdown("**Complete three-month forecast paths**")
        three_step = comparison.loc[comparison.horizon_months == 3]
        display_table(
            three_step.drop(columns=["horizon_months"]),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            f"Each method makes {int(three_step.iloc[0].test_origins)} complete three-month forecasts, "
            "starting at the same historical dates. Calendar months overlap across these paths, so "
            "forecast_values is a count of predictions, not a count of independent observed months. "
            "Errors combine all three leads; no 2025 actuals are available."
        )
        st.markdown("**Selected method: observed one-month errors**")
        display_table(back, hide_index=True, width="stretch")
        csv_download(
            "Download selected-method backtest",
            back.assign(model=method),
            "forecast_backtest.csv",
            "backtest_export",
        )
        csv_download(
            "Download model comparison",
            comparison,
            "forecast_model_comparison.csv",
            "comparison_export",
        )
    metadata = {
        "scope": grain,
        "entity": entity,
        "method": method,
        "scenario_pct": scenario,
        "history_months": m.month.dt.strftime("%Y-%m-%d").tolist(),
        "forecast_months": out.month.dt.strftime("%Y-%m-%d").tolist(),
        "filtered_transactions": len(subset),
        "filtered_skus": int(subset["product"].nunique()),
        "filter_values": {
            column: sorted(subset[column].unique().tolist())
            for column in [
                "division",
                "category",
                "brand",
                "product",
                "customer_type",
                "country",
                "channel",
            ]
            if column in subset
        },
        "unit": "EA",
        "quantity_type": "signed_net_demand",
        "returns_included": True,
        "scenario_rule": "baseline * (1 + scenario_pct / 100)",
        "one_step_test_origins": int(one_step.iloc[0].test_origins),
        "three_step_test_origins": int(three_step.iloc[0].test_origins),
        "three_step_paths_overlap": True,
        "limitations": [
            "Only selected 2024 monthly history is used.",
            "January–March 2025 values are estimates, not actuals or purchase requirements.",
            "No learned annual seasonality, inventory, supplier lead times or confidence bounds.",
            "Historical test errors do not guarantee future results.",
        ],
    }
    st.download_button(
        "Download forecast review pack",
        forecast_review_bundle(
            estimate_export, back.assign(model=method), comparison, paths, metadata
        ),
        file_name="supplyiq_forecast_review.zip",
        mime="application/zip",
        key="forecast_review_pack",
        help="Includes estimates, model comparisons, all test paths and the filters/assumptions used.",
    )
    st.info(
        "Planner action: investigate large customer orders, promotions and returns before applying a scenario. Assess forecast uncertainty with more history; no unsupported confidence interval is shown."
    )


def assistant(data, months, thresholds, scope):
    from .assistant_ui import render_assistant

    render_assistant(data, months, thresholds, scope)


def quality(data, report, filtered, months):
    from .reporting import review_records

    st.header("Data quality & totals")
    flagged = review_records(filtered)
    counters = st.columns(4)
    counters[0].metric("Selected transactions", f"{len(filtered):,}", border=True)
    counters[1].metric(
        "Selected SKUs", f"{filtered['product'].nunique():,}", border=True
    )
    counters[2].metric("Selected rows to review", f"{len(flagged):,}", border=True)
    counters[3].metric(
        "Source totals reconciled", "Yes" if report["reconciled"] else "No", border=True
    )
    st.success(
        "Sales records match the product and customer lists. Row counts and totals are unchanged."
        if report["reconciled"]
        else "Some totals do not match and need checking."
    )
    st.caption(
        "Workbook validation covers the whole workbook. Selected-data results and review records follow your current filters."
    )
    with st.expander("Inspect flagged records in your selection"):
        st.caption(
            "These are review candidates, not confirmed errors. Negative returns alone are expected and are not flagged. Source rows are retained unchanged."
        )
        if flagged.empty:
            st.success(
                "No sign differences, exact repeated rows or nonzero values with zero quantity in this selection."
            )
        else:
            display_table(flagged, hide_index=True, width="stretch")
            csv_download(
                "Download flagged records",
                flagged,
                "records_for_review.csv",
                "issue_records_export",
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
