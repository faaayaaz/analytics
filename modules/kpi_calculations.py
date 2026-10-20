import numpy as np
import pandas as pd
from .data_loader import MONTHS


def ratio(numerator, denominator, percent=False, require_positive=True):
    return (
        float(numerator / denominator * (100 if percent else 1))
        if pd.notna(denominator)
        and (denominator > 0 if require_positive else denominator != 0)
        else np.nan
    )


def growth(current, previous):
    return ratio(current - previous, previous, True)


def kpis(data, months):
    sales = data.sales.sum()
    cost = data.cost.sum()
    qty = data.quantity.sum()
    selected = sorted(pd.to_datetime(months))
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
    m = (
        data.groupby("month")[["quantity", "sales", "cost"]]
        .sum()
        .reindex(pd.DatetimeIndex(months), fill_value=0)
    )
    m.index.name = "month"
    m["growth_pct"] = (
        [np.nan]
        + [growth(a, b) for a, b in zip(m.quantity.iloc[1:], m.quantity.iloc[:-1])]
        if len(m)
        else []
    )
    return m.reset_index()


def group_summary(data, dimension):
    out = (
        data.groupby(dimension, dropna=False)[["sales", "quantity", "cost"]]
        .sum()
        .reset_index()
    )
    out["gross_profit"] = out.sales - out.cost
    out["margin_pct"] = np.where(
        out.sales != 0, out.gross_profit / out.sales * 100, np.nan
    )
    return out.sort_values("sales", ascending=False)


def executive_insights(data, months):
    if data.empty:
        return ["No records match the selected filters."]
    k = kpis(data, months)
    lines = []
    div = group_summary(data, "division").iloc[0]
    share = ratio(div.sales, data.sales.sum(), True)
    lines.append(
        f"{div.division} leads this selection with AED {div.sales:,.2f} in net sales ({share:.1f}% of net sales)."
    )
    top = group_summary(data, "product").head(10)
    lines.append(
        f"The top 10 products make up {ratio(top.sales.sum(), data.sales.sum(), True):.1f}% of sales after returns in your selection. Check how much the plan depends on these products."
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
    lines.append(
        f"Returned or credited units equal {k['Negative Transaction Quantity Rate %']:.2f}% of positive units sold. Review credit notes separately to understand the demand behind the total."
    )
    return lines
