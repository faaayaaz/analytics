"""Readable table headings without changing calculations or exported column names."""

import streamlit as st

COLUMN_LABELS = {
    "product": "Product code",
    "brand": "Brand",
    "division": "Division",
    "category": "Category",
    "month": "Month",
    "measure": "Measure",
    "positive_total": "Positive total",
    "negative_total": "Returns/credits total",
    "net_total": "Total after returns/credits",
    "model": "Forecast method",
    "customer": "Customer",
    "country": "Country",
    "customer_type": "Customer type",
    "channel": "Sales channel",
    "uom": "Unit of measure",
    "margin_pct": "Gross margin (%)",
    "gross_profit": "Gross profit (AED)",
    "sales": "Sales after returns (AED)",
    "net_sales_aed": "Sales after returns (AED)",
    "quantity": "Units sold minus returns",
    "net_units": "Units sold minus returns",
    "cost": "Product costs (AED)",
    "demand_cv": "Demand consistency score (CV)",
    "abc": "Sales value group (ABC)",
    "xyz": "Demand consistency group (XYZ)",
    "segment": "Combined group",
    "contribution_pct": "Share of positive sales (%)",
    "cumulative_pct": "Running share of positive sales (%)",
    "average_monthly_demand": "Monthly average (units ÷ 12)",
    "selected_month_mean": "Average in selected months",
    "gross_margin_pct": "Gross margin (%)",
    "monthly_demand_growth_pct": "Change from previous month (%)",
    "negative_quantity_rate_pct": "Returned/credited units (%)",
    "planning_priority": "Suggested review",
    "growth_pct": "Change from previous month (%)",
    "baseline": "Original forecast (units)",
    "scenario_estimate": "Forecast with your change (units)",
    "actual": "Actual units",
    "predicted": "Forecast units",
    "error": "Forecast minus actual (units)",
    "previous_units": "Previous month units",
    "latest_units": "Latest month units",
    "prior_3m_mean": "Average of previous 3 months",
    "standardized_deviation": "Size of unusual change (standard deviations)",
}


def display_table(data, **kwargs):
    if "measure" in data.columns:
        data = data.copy()
        data["measure"] = data["measure"].replace(
            {"quantity": "Units", "sales": "Sales (AED)", "cost": "Product costs (AED)"}
        )
    if "planning_priority" in data.columns:
        data = data.copy()
        readable = {
            "Review nonpositive revenue / demand": "Review sales or average units of zero or less",
            "Protect stable high-value demand plan": "Review important products with steady demand",
            "Investigate high-value volatility": "Check important products with large demand swings",
            "Investigate decline ≥20%": "Check a demand drop of 20% or more",
            "Validate growth ≥20%": "Check a demand rise of 20% or more",
            "Review negative quantities >5%": "Review returned/credited units above 5%",
            "Review low revenue contribution": "Review products with a small share of sales",
            "Monitor baseline demand": "Keep watching normal demand",
        }
        data["planning_priority"] = data["planning_priority"].map(
            lambda value: "; ".join(
                readable.get(part, part) for part in value.split("; ")
            )
        )
    config = {
        column: st.column_config.Column(column, help=label)
        for column, label in COLUMN_LABELS.items()
        if column in data.columns
    }
    config.update(kwargs.pop("column_config", {}))
    return st.dataframe(data, column_config=config, **kwargs)
