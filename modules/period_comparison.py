"""Like-for-like calendar comparisons restricted to the supplied 2024 history."""

import pandas as pd
from .data_loader import MONTHS
from .kpi_calculations import kpis, growth


def compare_period(data, months, available_months=None):
    current = pd.DatetimeIndex(sorted(set(pd.to_datetime(months))))
    result = {
        "available": False,
        "reason": "Select consecutive months to compare equal-length periods.",
    }
    if not len(current) or not current.equals(
        pd.date_range(current[0], current[-1], freq="MS")
    ):
        return result
    previous = pd.date_range(
        current[0] - pd.offsets.MonthBegin(len(current)),
        periods=len(current),
        freq="MS",
    )
    if not current.isin(MONTHS).all() or not previous.isin(MONTHS).all():
        result["reason"] = (
            "The previous period is outside the 2024 workbook. Try Q4 or the last six months."
        )
        return result
    coverage = (
        MONTHS if available_months is None else pd.DatetimeIndex(available_months)
    )
    if not current.isin(coverage).all() or not previous.isin(coverage).all():
        result["reason"] = (
            "The workbook has missing months in one of these periods; confirm source coverage before comparing."
        )
        return result
    current_rows = data.loc[data.month.isin(current)]
    prior_rows = data.loc[data.month.isin(previous)]
    now = kpis(current_rows, current)
    before = kpis(prior_rows, previous)
    deltas = {}
    for name in list(now)[:3]:
        deltas[name] = growth(now[name], before[name])
    name = "Gross Margin %"
    deltas[name] = (
        now[name] - before[name]
        if pd.notna(now[name]) and pd.notna(before[name])
        else float("nan")
    )
    label = (
        previous[0].strftime("%b %Y")
        if len(previous) == 1
        else previous[0].strftime("%b") + "–" + previous[-1].strftime("%b %Y")
    )
    return {
        "available": True,
        "reason": "",
        "previous_months": list(previous),
        "label": label,
        "current": now,
        "previous": before,
        "deltas": deltas,
    }
