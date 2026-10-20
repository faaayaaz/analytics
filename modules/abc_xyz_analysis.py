import numpy as np
import pandas as pd
from .kpi_calculations import ratio, growth
from .data_loader import MONTHS


def classify(data, months=MONTHS, a=80.0, b=95.0, x=0.5, y=1.0):
    if not 0 < a < b < 100 or not 0 <= x < y:
        raise ValueError("Thresholds must satisfy 0 < A < B < 100 and 0 ≤ X < Y.")
    dims = ["product", "brand", "division", "category"]
    out = (
        data.groupby(dims, dropna=False)[["sales", "quantity", "cost"]]
        .sum()
        .reset_index()
        .sort_values(["sales", "product"], ascending=[False, True])
        .reset_index(drop=True)
    )
    if out.empty:
        return out
    eligible = out.sales.clip(lower=0).sum()
    out["contribution_pct"] = (
        out.sales.where(out.sales > 0, 0) / eligible * 100 if eligible > 0 else np.nan
    )
    out["cumulative_pct"] = out.contribution_pct.cumsum()
    # The SKU crossing a boundary belongs to the segment it starts in.
    prior = out.cumulative_pct - out.contribution_pct
    out["abc"] = np.select(
        [out.sales <= 0, prior < a, prior < b], ["N", "A", "B"], default="C"
    )
    series = (
        data.groupby(["product", "month"])
        .quantity.sum()
        .unstack(fill_value=0)
        .reindex(columns=pd.DatetimeIndex(months), fill_value=0)
    )
    means = series.mean(axis=1)
    std = series.std(axis=1, ddof=0)
    cv = std / means.where(means > 0)
    out["demand_cv"] = out["product"].map(cv)
    out["average_monthly_demand"] = out.quantity / 12
    out["selected_month_mean"] = out["product"].map(means)
    out["xyz"] = np.select(
        [out.demand_cv.isna(), out.demand_cv <= x, out.demand_cv <= y],
        ["N", "X", "Y"],
        default="Z",
    )
    out["gross_margin_pct"] = [
        ratio(s - c, s, True, require_positive=False)
        for s, c in zip(out.sales, out.cost)
    ]
    ordered = sorted(months)
    changes = {}
    if len(ordered) >= 2 and ordered[-1] - pd.offsets.MonthBegin(1) == ordered[-2]:
        changes = {
            sku: growth(row.iloc[-1], row.iloc[-2]) for sku, row in series.iterrows()
        }
    out["monthly_demand_growth_pct"] = out["product"].map(changes)
    pos = data.quantity.clip(lower=0).groupby(data["product"]).sum()
    neg = (-data.quantity.clip(upper=0)).groupby(data["product"]).sum()
    rates = neg / pos.where(pos > 0) * 100
    out["negative_quantity_rate_pct"] = out["product"].map(rates)
    out["segment"] = out.abc + out.xyz
    out["planning_priority"] = out.apply(priority, axis=1)
    return out


def priority(row):
    signals = []
    if row.abc == "N" or row.xyz == "N":
        signals.append("Review nonpositive revenue / demand")
    if row.abc == "A" and row.xyz == "X":
        signals.append("Protect stable high-value demand plan")
    if row.abc == "A" and row.xyz == "Z":
        signals.append("Investigate high-value volatility")
    if row.monthly_demand_growth_pct <= -20:
        signals.append("Investigate decline ≥20%")
    if row.monthly_demand_growth_pct >= 20:
        signals.append("Validate growth ≥20%")
    if row.negative_quantity_rate_pct > 5:
        signals.append("Review negative quantities >5%")
    if row.abc == "C":
        signals.append("Review low revenue contribution")
    return "; ".join(signals) or "Monitor baseline demand"


RECOMMENDATIONS = {
    "AX": "Review demand regularly. Check planned promotions and confirmed customer orders.",
    "AY": "Each month, check why demand changed and where the forecast missed actual sales.",
    "AZ": "Start by checking which customers cause large demand swings. Compare a few possible demand changes.",
    "BX": "Review demand regularly and use a simple forecast as a starting point.",
    "BY": "Check month-to-month changes and whether different customers are buying.",
    "BZ": "Check occasional purchases and unusually large orders before changing the plan.",
    "CX": "Review whether keeping these products makes business sense. Match review effort to their sales value.",
    "CY": "Discuss the sales value and uneven demand with the sales team.",
    "CZ": "Check whether customers still need these products. Review credit notes and occasional purchases.",
}
