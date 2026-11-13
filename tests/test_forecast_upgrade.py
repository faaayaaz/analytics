import io
import json
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest

from modules.forecasting import (
    METHODS,
    compare_models,
    forecast,
    forecast_review_bundle,
    predict,
    rolling_backtest,
)


def history(values=None):
    return pd.DataFrame(
        {
            "month": pd.date_range("2024-01-01", periods=12, freq="MS"),
            "quantity": values
            if values is not None
            else [100, 110, 90, 120, 150, 160, 130, 140, 170, 180, 190, 220],
        }
    )


def test_comparisons_use_identical_observations_and_training_cutoffs():
    monthly = history()
    comparison, paths = compare_models(monthly)
    assert len(comparison) == 4
    for horizon, origins, predictions in [(1, 9, 9), (3, 7, 21)]:
        rows = comparison.loc[comparison.horizon_months == horizon]
        assert set(rows.model) == set(METHODS)
        assert set(rows.test_origins) == {origins}
        assert set(rows.forecast_values) == {predictions}
        a = paths.loc[
            (paths.model == METHODS[0]) & (paths.test_horizon_months == horizon)
        ]
        b = paths.loc[
            (paths.model == METHODS[1]) & (paths.test_horizon_months == horizon)
        ]
        pd.testing.assert_frame_equal(
            a[["training_end", "month", "horizon_month", "actual"]].reset_index(
                drop=True
            ),
            b[["training_end", "month", "horizon_month", "actual"]].reset_index(
                drop=True
            ),
        )
        assert (a.training_end < a.month).all()
    three = paths.loc[(paths.model == METHODS[0]) & (paths.test_horizon_months == 3)]
    first = three.iloc[:3]
    assert first.training_end.nunique() == 1 and list(first.horizon_month) == [1, 2, 3]
    expected = predict(monthly.quantity.iloc[:3], horizon=3)
    assert np.allclose(first.predicted, expected)
    assert (
        three.month.duplicated().any()
    )  # Review pack must disclose overlapping paths.


def test_three_step_predictions_do_not_look_ahead():
    original = history()
    changed = original.copy()
    changed.loc[3:, "quantity"] = -99999
    a = rolling_backtest(original, horizon=3).iloc[:3]
    b = rolling_backtest(changed, horizon=3).iloc[:3]
    assert np.allclose(a.predicted, b.predicted)
    assert not np.allclose(a.actual, b.actual)


@pytest.mark.parametrize(
    "mutation", ["duplicates", "infinite", "nan", "gap", "outside_year", "bad_date"]
)
def test_forecast_rejects_invalid_monthly_input(mutation):
    frame = history()
    frame["quantity"] = frame["quantity"].astype(float)
    if mutation == "duplicates":
        frame.loc[2, "month"] = frame.loc[1, "month"]
    elif mutation == "infinite":
        frame.loc[2, "quantity"] = float("inf")
    elif mutation == "nan":
        frame.loc[2, "quantity"] = float("nan")
    elif mutation == "gap":
        frame = frame.drop(index=4)
    elif mutation == "bad_date":
        frame["month"] = frame["month"].astype(object)
        frame.loc[2, "month"] = "not a date"
    else:
        frame.loc[0, "month"] = pd.Timestamp("2023-01-01")
    with pytest.raises(ValueError):
        forecast(frame)


def test_bad_methods_scenarios_and_horizons_cannot_silently_change_models():
    with pytest.raises(ValueError):
        predict([1, 2, 3], method="unknown")
    with pytest.raises(ValueError):
        forecast(history(), method="unknown")
    for scenario in [float("nan"), float("inf"), -101, "bad"]:
        with pytest.raises(ValueError):
            forecast(history(), scenario=scenario)
    for horizon in [0, -1, True, 1.5]:
        with pytest.raises(ValueError):
            predict([1, 2, 3], horizon=horizon)
    with pytest.raises(ValueError):
        rolling_backtest(history(), horizon=4)


def test_signed_net_estimates_and_zero_denominators_are_preserved():
    values = history([-10] * 12)
    out, _, _ = forecast(values, scenario=20)
    assert list(out.baseline) == [-10, -10, -10]
    assert list(out.scenario_estimate) == [-12, -12, -12]
    assert list(out.horizon_month) == [1, 2, 3]
    comparison, _ = compare_models(history([0] * 12))
    assert comparison["WAPE %"].isna().all()
    assert comparison["Bias %"].isna().all()
    assert (comparison.MAE == 0).all()


def test_review_pack_reconciles_estimates_errors_and_metadata():
    frame = history()
    out, back, _ = forecast(frame, scenario=20)
    comparison, paths = compare_models(frame)
    metadata = {
        "scenario_pct": 20,
        "scope": "Selected portfolio",
        "history_months": 12,
        "three_step_paths_overlap": True,
    }
    payload = forecast_review_bundle(out, back, comparison, paths, metadata)
    with ZipFile(io.BytesIO(payload)) as archive:
        assert set(archive.namelist()) == {
            "forecast_estimates.csv",
            "selected_model_backtest.csv",
            "model_comparison.csv",
            "all_backtest_paths.csv",
            "assumptions.json",
        }
        exported = pd.read_csv(archive.open("forecast_estimates.csv"))
        assert exported.baseline.sum() == pytest.approx(out.baseline.sum())
        assert exported.scenario_estimate.sum() == pytest.approx(
            out.baseline.sum() * 1.2
        )
        assert json.loads(archive.read("assumptions.json")) == metadata
        assert len(pd.read_csv(archive.open("all_backtest_paths.csv"))) == 60
