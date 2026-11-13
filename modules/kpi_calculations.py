import numpy as np
import pandas as pd
from .data_loader import MONTHS


def ratio(numerator, denominator, percent=False, require_positive=True):
    """Return N/A for undefined or non-finite ratios, retaining signed margins."""
    try:
        numerator, denominator = float(numerator), float(denominator)
    except (TypeError, ValueError):
        return np.nan
    if not np.isfinite([numerator, denominator]).all():
        return np.nan
    invalid_denominator = denominator <= 0 if require_positive else denominator == 0
    if invalid_denominator:
        return np.nan
    result = numerator / denominator * (100 if percent else 1)
    return float(result) if np.isfinite(result) else np.nan


def _selected_months(months):
    """Canonical calendar selection; UI and callers need not pre-sort it."""
    return pd.DatetimeIndex(months).dropna().unique().sort_values()


def growth(current, previous):
    return ratio(current - previous, previous, True)


def kpis(data, months):
    selected = _selected_months(months)
    data = data.loc[data.month.isin(selected)]
    sales = data.sales.sum()
    cost = data.cost.sum()
    qty = data.quantity.sum()
    monthly = monthly_demand(data, selected)
    # Only adjacent calendar months that are BOTH in the selection support selected-scope MoM.
    mom = np.nan
    if len(selected) >= 2 and selected[-1] - pd.offsets.MonthBegin(1) == selected[-2]:
        mom = growth(monthly.quantity.iloc[-1], monthly.quantity.iloc[-2])
    return {
        "Net Sales (AED)": sales,
        "Net Units Sold": qty,
        "Gross Profit (AED)": sales - cost,
        "Gross Margin %": ratio(sales - cost, sales, True, require_positive=False),
        "MoM Demand Growth %": mom,
        "Active SKUs": data["product"].nunique(),
        "Average Monthly Net Demand": qty / 12,
        "Negative Transaction Quantity Rate %": ratio(
            -data.loc[data.quantity < 0, "quantity"].sum(),
            data.loc[data.quantity > 0, "quantity"].sum(),
            True,
        ),
    }


def monthly_demand(data, months=MONTHS):
    selected = _selected_months(months)
    m = (
        data.groupby("month")[["quantity", "sales", "cost"]]
        .sum()
        .reindex(selected, fill_value=0)
    )
    m.index.name = "month"
    m["growth_pct"] = np.nan
    for i in range(1, len(m)):
        if m.index[i - 1] + pd.offsets.MonthBegin(1) == m.index[i]:
            m.iloc[i, m.columns.get_loc("growth_pct")] = growth(
                m.quantity.iloc[i], m.quantity.iloc[i - 1]
            )
    return m.reset_index()


def group_summary(data, dimension):
    out = (
        data.groupby(dimension, dropna=False)[["sales", "quantity", "cost"]]
        .sum()
        .reset_index()
    )
    out["gross_profit"] = out.sales - out.cost
    out["margin_pct"] = out.gross_profit.div(out.sales.where(out.sales.ne(0))).mul(100)
    return out.sort_values("sales", ascending=False)


def executive_insights(data, months):
    months = _selected_months(months)
    data = data.loc[data.month.isin(months)]
    if data.empty:
        return ["No records match the selected filters."]
    k = kpis(data, months)
    lines = []
    div = group_summary(data, "division").iloc[0]
    share = ratio(div.sales, data.sales.sum(), True)
    if pd.notna(share):
        lines.append(
            f"{div.division} leads this selection with AED {div.sales:,.2f} in net sales ({share:.1f}% of net sales)."
        )
    else:
        lines.append(
            f"{div.division} has the highest net sales in this selection at AED {div.sales:,.2f}. Sales contribution is N/A because total net sales are zero or negative."
        )
    top = group_summary(data, "product").head(10)
    top_share = ratio(top.sales.sum(), data.sales.sum(), True)
    if pd.notna(top_share):
        lines.append(
            f"The top 10 products make up {top_share:.1f}% of sales after returns in your selection. Check how much the plan depends on these products."
        )
    else:
        lines.append(
            "Product revenue contribution is N/A because total net sales are zero or negative. Review credits and returns before interpreting concentration."
        )
    m = monthly_demand(data, sorted(months))
    valid = []
    for i in range(1, len(m)):
        if m.month.iloc[i] - pd.offsets.MonthBegin(1) == m.month.iloc[
            i - 1
        ] and pd.notna(m.growth_pct.iloc[i]):
            valid.append(i)
    if valid:
        i = max(valid, key=lambda j: abs(m.growth_pct.iloc[j]))
        lines.append(
            f"Largest change from the previous month: {m.month.iloc[i]:%b %Y}, {m.growth_pct.iloc[i]:+.1f}% versus {m.month.iloc[i - 1]:%b} ({m.quantity.iloc[i]:,.0f} units after returns). Check which customers and products caused the change before updating the plan."
        )
    rate = k["Negative Transaction Quantity Rate %"]
    if pd.notna(rate):
        lines.append(
            f"Returned or credited units equal {rate:.2f}% of positive units sold. Review credit notes separately to understand the demand behind the total."
        )
    else:
        lines.append(
            "Negative quantity rate is N/A because this selection has no positive units sold. Review return-only or credit activity separately."
        )
    return lines
