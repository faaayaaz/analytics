"""Explainable signed net-demand forecasts, comparable backtests and review exports.

These estimates do not contain inventory, supplier or purchase calculations.
"""

from io import BytesIO
import json
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import pandas as pd
from .kpi_calculations import ratio

METHODS = ("3-month moving average", "Simple exponential smoothing")


def _method(method):
    if method not in METHODS:
        raise ValueError("Choose a supported forecast method: " + ", ".join(METHODS))


def _monthly_values(monthly):
    """Reject gaps/duplicates rather than silently changing the time series."""
    if not {"month", "quantity"}.issubset(monthly.columns):
        raise ValueError("Forecast input needs month and quantity columns.")
    ordered = monthly.copy()
    ordered["month"] = pd.to_datetime(ordered["month"], errors="coerce")
    if ordered["month"].isna().any():
        raise ValueError("Monthly dates must be valid first-of-month dates in 2024.")
    ordered = ordered.sort_values("month")
    dates = pd.DatetimeIndex(ordered["month"])
    values = pd.to_numeric(ordered["quantity"], errors="coerce").to_numpy(
        dtype=float, na_value=np.nan
    )
    if not np.isfinite(values).all():
        raise ValueError("Monthly demand must contain finite numeric quantities.")
    if (
        len(dates) < 6
        or dates.isna().any()
        or not dates.equals(pd.date_range(dates[0], dates[-1], freq="MS"))
    ):
        raise ValueError(
            "Select at least six consecutive months for backtesting and forecasting."
        )
    if (dates.year != 2024).any() or dates[-1] != pd.Timestamp("2024-12-01"):
        raise ValueError(
            "Include December 2024 to estimate January–March 2025 without using excluded months."
        )
    return dates, values


def predict(history, method="3-month moving average", horizon=3):
    _method(method)
    if (
        not isinstance(horizon, (int, np.integer))
        or isinstance(horizon, bool)
        or horizon < 1
    ):
        raise ValueError("Forecast horizon must be a positive whole number of months.")
    try:
        values = list(map(float, history))
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "At least three finite monthly observations are required."
        ) from exc
    if len(values) < 3 or not np.isfinite(values).all():
        raise ValueError("At least three finite monthly observations are required.")
    if method == "Simple exponential smoothing":
        level = values[0]
        for value in values[1:]:
            level = 0.3 * value + 0.7 * level
        return [level] * horizon
    estimates = []
    for _ in range(horizon):
        value = float(np.mean(values[-3:]))
        estimates.append(value)
        values.append(value)
    return estimates


def score_errors(back):
    """Positive signed error means the estimate was above actual net demand."""
    denominator = back["actual"].abs().sum()
    return {
        "MAE": float(back["error"].abs().mean()),
        "WAPE %": ratio(back["error"].abs().sum(), denominator, True),
        "Bias %": ratio(back["error"].sum(), denominator, True),
        "Mean bias (units)": float(back["error"].mean()),
        "Backtest periods": len(back),
    }


def rolling_backtest(monthly, method="3-month moving average", horizon=1):
    """Forecast complete future paths using only observations before each origin.

    Three-month paths overlap in calendar months. Each origin/lead is a forecast,
    not an independent actual month; provenance is retained for review.
    """
    _method(method)
    if (
        not isinstance(horizon, (int, np.integer))
        or isinstance(horizon, bool)
        or not 1 <= horizon <= 3
    ):
        raise ValueError("Backtest horizon must be one, two or three months.")
    dates, values = _monthly_values(monthly)
    rows = []
    for train_size in range(3, len(values) - horizon + 1):
        estimates = predict(values[:train_size], method, horizon)
        for lead, estimate in enumerate(estimates, start=1):
            position = train_size + lead - 1
            actual = float(values[position])
            rows.append(
                {
                    "training_end": dates[train_size - 1],
                    "month": dates[position],
                    "horizon_month": lead,
                    "actual": actual,
                    "predicted": estimate,
                    "error": estimate - actual,
                }
            )
    return pd.DataFrame(rows)


def forecast(monthly, method="3-month moving average", scenario=0):
    _method(method)
    _, values = _monthly_values(monthly)
    try:
        scenario = float(scenario)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Demand scenario must be a finite percentage of at least −100%."
        ) from exc
    if not np.isfinite(scenario) or scenario < -100:
        raise ValueError(
            "Demand scenario must be a finite percentage of at least −100%."
        )
    back = rolling_backtest(monthly, method, horizon=1)
    metrics = score_errors(back)
    baseline = predict(values, method, 3)
    out = pd.DataFrame(
        {
            "month": pd.date_range("2025-01-01", periods=3, freq="MS"),
            "horizon_month": [1, 2, 3],
            "baseline": baseline,
        }
    )
    out["scenario_estimate"] = out["baseline"] * (1 + scenario / 100)
    out["change_units"] = out["scenario_estimate"] - out["baseline"]
    return out, back, metrics


def compare_models(monthly):
    """Both models use the same origins and held-out observations for each design."""
    rows, paths = [], []
    for horizon in (1, 3):
        for method in METHODS:
            back = rolling_backtest(monthly, method, horizon)
            scores = score_errors(back)
            scores.pop(
                "Backtest periods"
            )  # Paths count predictions, not independent calendar months.
            rows.append(
                {
                    "model": method,
                    "horizon_months": horizon,
                    "test_origins": int(back["training_end"].nunique()),
                    "forecast_values": len(back),
                    **scores,
                }
            )
            paths.append(back.assign(model=method, test_horizon_months=horizon))
    return pd.DataFrame(rows), pd.concat(paths, ignore_index=True)


def forecast_review_bundle(estimates, backtest, comparison, paths, metadata):
    """Keep estimates, observed errors and assumptions together in a portable ZIP."""
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for name, frame in [
            ("forecast_estimates.csv", estimates),
            ("selected_model_backtest.csv", backtest),
            ("model_comparison.csv", comparison),
            ("all_backtest_paths.csv", paths),
        ]:
            archive.writestr(name, frame.to_csv(index=False).encode("utf-8-sig"))
        archive.writestr(
            "assumptions.json",
            json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False),
        )
    return buffer.getvalue()
