"""Nonseasonal, signed net-demand estimates; no inventory or purchase calculations."""

import numpy as np
import pandas as pd
from .kpi_calculations import ratio


def predict(history, method="3-month moving average", horizon=3):
    values = list(map(float, history))
    if len(values) < 3:
        raise ValueError("At least three contiguous monthly observations are required.")
    if method == "Simple exponential smoothing":
        level = values[0]
        for v in values[1:]:
            level = 0.3 * v + 0.7 * level
        return [level] * horizon
    forecasts = []
    for _ in range(horizon):
        value = float(np.mean(values[-3:]))
        forecasts.append(value)
        values.append(value)
    return forecasts


def forecast(monthly, method="3-month moving average", scenario=0):
    monthly = monthly.sort_values("month")
    # Calendar gaps cannot be treated as consecutive observations.
    dates = pd.DatetimeIndex(monthly.month)
    if len(dates) < 6 or not dates.equals(
        pd.date_range(dates[0], dates[-1], freq="MS")
    ):
        raise ValueError(
            "Select at least six consecutive months for backtesting and forecasting."
        )
    if dates[-1] != pd.Timestamp("2024-12-01"):
        raise ValueError(
            "Include December 2024 to estimate January–March 2025 without using excluded months."
        )
    values = monthly.quantity.to_numpy(dtype=float)
    rows = []
    for i in range(3, len(values)):
        pred = predict(values[:i], method, 1)[0]
        rows.append(
            {
                "month": dates[i],
                "actual": values[i],
                "predicted": pred,
                "error": pred - values[i],
            }
        )
    back = pd.DataFrame(rows)
    metrics = {
        "MAE": float(back.error.abs().mean()),
        "WAPE %": ratio(back.error.abs().sum(), back.actual.abs().sum(), True),
        "Bias %": ratio(back.error.sum(), back.actual.abs().sum(), True),
        "Mean bias (units)": float(back.error.mean()),
        "Backtest periods": len(back),
    }
    baseline = predict(values, method, 3)
    out = pd.DataFrame(
        {
            "month": pd.date_range("2025-01-01", periods=3, freq="MS"),
            "baseline": baseline,
        }
    )
    out["scenario_estimate"] = out.baseline * (1 + scenario / 100)
    return out, back, metrics
