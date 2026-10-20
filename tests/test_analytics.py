import io
from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest
from modules.data_loader import load_workbook, MONTHS, filter_data
from modules.kpi_calculations import kpis, ratio, growth, monthly_demand
from modules.abc_xyz_analysis import classify
from modules.forecasting import forecast, predict
from modules.ai_assistant import answer


@pytest.fixture(scope="session")
def workbook():
    return load_workbook()


def test_real_workbook_reconciliation(workbook):
    d, r = workbook
    assert len(d) == 160572 and r["reconciled"]
    assert d["product"].nunique() == 250 and d.customer.nunique() == 292
    assert d.sales.sum() == pytest.approx(441894325.26)
    assert d.cost.sum() == pytest.approx(334029937.73)
    assert d.quantity.sum() == 22323030
    assert r["sign_mismatch_rows"] == 11
    assert not any(
        v
        for k, v in r.items()
        if "master_mismatch" in k or "unmatched" in k or "duplicate" in k
    )
    k = kpis(d, MONTHS)
    assert k["Gross Profit (AED)"] == pytest.approx(107864387.53)
    assert k["Gross Margin %"] == pytest.approx(107864387.53 / 441894325.26 * 100)
    assert k["Negative Transaction Quantity Rate %"] == pytest.approx(
        0.7544395245324665
    )
    assert k["Average Monthly Net Demand"] == 22323030 / 12


def test_metrics_undefined_and_signed(workbook):
    assert np.isnan(ratio(1, 0)) and np.isnan(growth(10, -2))
    d, _ = workbook
    negative = d.loc[d.quantity < 0]
    assert np.isnan(kpis(negative, MONTHS)["Negative Transaction Quantity Rate %"])
    assert np.isnan(
        kpis(d.loc[d.month.isin([MONTHS[0], MONTHS[2]])], [MONTHS[0], MONTHS[2]])[
            "MoM Demand Growth %"
        ]
    )


def test_abc_xyz_full_workbook(workbook):
    d, _ = workbook
    s = classify(d)
    assert s.contribution_pct.sum() == pytest.approx(100)
    assert set(s.segment).issubset({a + b for a in "ABCN" for b in "XYZN"})
    assert len(s) == 250
    assert s.sales.sum() == pytest.approx(d.sales.sum())
    assert s.average_monthly_demand.sum() == pytest.approx(d.quantity.sum() / 12)


def synthetic():
    rows = []
    for sku, sales, quantities in [
        ("P001", 80, [10] * 12),
        ("P002", 15, [0] * 11 + [120]),
        ("P003", 5, [0] * 12),
        ("P004", -2, [-1] * 12),
    ]:
        for month, q in zip(MONTHS, quantities):
            rows.append(
                dict(
                    product=sku,
                    brand="Brand 1",
                    division="Food",
                    category="Test",
                    sales=sales / 12,
                    quantity=q,
                    cost=sales / 24,
                    month=month,
                )
            )
    return pd.DataFrame(rows)


def test_classification_edges():
    s = classify(synthetic()).set_index("product")
    assert (
        s.loc["P001", "abc"] == "A"
        and s.loc["P002", "abc"] == "B"
        and s.loc["P003", "abc"] == "C"
    )
    assert s.loc["P001", "xyz"] == "X" and s.loc["P002", "xyz"] == "Z"
    assert s.loc["P003", "xyz"] == "N" and np.isnan(s.loc["P003", "demand_cv"])
    assert s.loc["P004", "abc"] == "N" and s.loc["P004", "xyz"] == "N"
    assert s.loc["P002", "demand_cv"] == pytest.approx(np.sqrt(11))
    with pytest.raises(ValueError):
        classify(synthetic(), a=95, b=80)


def test_filters_and_excluded_months(workbook):
    d, _ = workbook
    f = filter_data(d, {"division": ["Food"], "brand": ["Brand 10"]}, MONTHS[-3:])
    assert (
        set(f.division) == {"Food"}
        and set(f.brand) == {"Brand 10"}
        and f.month.nunique() == 3
    )
    t = classify(f, MONTHS[-3:])
    assert t.selected_month_mean.sum() == pytest.approx(f.quantity.sum() / 3)
    assert t.average_monthly_demand.sum() == pytest.approx(f.quantity.sum() / 12)
    assert filter_data(d, {}, []).empty


def test_forecast_rolling_no_leakage(workbook):
    d, _ = workbook
    m = monthly_demand(d)
    out, back, metrics = forecast(m)
    assert len(out) == 3 and list(out.month.dt.year) == [2025] * 3
    assert len(back) == 9 and metrics["Backtest periods"] == 9
    assert back.predicted.iloc[0] == pytest.approx(m.quantity.iloc[:3].mean())
    assert out.baseline.iloc[0] == pytest.approx(m.quantity.iloc[-3:].mean())
    assert metrics["WAPE %"] == pytest.approx(
        back.error.abs().sum() / back.actual.abs().sum() * 100
    )
    assert metrics["Bias %"] == pytest.approx(
        back.error.sum() / back.actual.abs().sum() * 100
    )
    scenario, _, _ = forecast(m, scenario=20)
    assert np.allclose(scenario.scenario_estimate, scenario.baseline * 1.2)
    zero = m.copy()
    zero.quantity = 0
    _, _, z = forecast(zero)
    assert z["MAE"] == 0 and np.isnan(z["WAPE %"])
    with pytest.raises(ValueError):
        forecast(m.iloc[:-1])
    with pytest.raises(ValueError):
        forecast(m.drop(index=3))
    assert predict([1, 2, 3], "Simple exponential smoothing")[0] == pytest.approx(1.81)


@pytest.mark.parametrize(
    "question,intent",
    [
        ("Which 10 SKUs generated the highest sales in 2024?", "top"),
        ("Which products have the most volatile monthly demand?", "volatile"),
        ("Compare demand patterns across Food and Personal Care.", "compare"),
        ("Which products belong to the AZ category?", "segment"),
        ("Which categories experienced declining demand?", "declining"),
        ("What was the monthly demand growth for Brand 10?", "growth"),
        ("Which SKUs should planners prioritize for investigation?", "priority"),
        ("Explain the ABC–XYZ classification of product P001.", "detail"),
        ("Identify significant demand anomalies.", "anomalies"),
        ("Summarize the main supply planning insights.", "summary"),
        ("What inventory should I replenish?", "unavailable"),
    ],
)
def test_assistant_questions(workbook, question, intent):
    d, _ = workbook
    r = answer(question, d, MONTHS)
    assert r["context"]["intent"] == intent and len(r["text"]) > 30
    if intent not in ["summary", "unavailable"]:
        assert r["table"] is not None


def test_assistant_scope_followup_and_safety(workbook):
    d, _ = workbook
    f = d.loc[d.division == "Food"]
    r = answer("top 10 SKUs by sales", f, MONTHS)
    expected = f.groupby("product").sales.sum().sort_values(ascending=False).head(10)
    assert r["table"]["product"].tolist() == expected.index.tolist()
    assert r["table"].net_sales_aed.sum() == pytest.approx(expected.sum())
    r2 = answer("What about Brand 10?", f, MONTHS, previous=r["context"])
    assert r2["context"]["intent"] == "top" and r2["context"]["brand"] == "Brand 10"
    assert set(r2["table"]["product"]).issubset(
        set(f.loc[f.brand == "Brand 10", "product"])
    )
    assert answer("DROP TABLE sales_data", d, MONTHS)["context"]["intent"] == "help"
    assert "absent" in answer("Explain product P999", d, MONTHS)["text"]
    with patch(
        "modules.ai_assistant.llm_route",
        side_effect=RuntimeError("simulated API failure"),
    ):
        fallback = answer("top 10 SKUs", d, MONTHS, api_key="test-placeholder")
        assert (
            fallback["context"]["intent"] == "top"
            and "API unavailable" in fallback["notice"]
        )


def test_negative_sales_margin_formula():
    d = synthetic().loc[lambda x: x["product"] == "P004"]
    assert kpis(d, MONTHS)["Gross Margin %"] == pytest.approx(50)
    assert classify(d).gross_margin_pct.iloc[0] == pytest.approx(50)


def test_optional_llm_uses_verified_evidence(workbook):
    d, _ = workbook
    with (
        patch("modules.ai_assistant.llm_route", return_value="top") as route,
        patch(
            "modules.ai_assistant.explain_verified",
            return_value="Review customer drivers for these leading products.",
        ) as explain,
    ):
        result = answer(
            "What are the sales leaders?", d, MONTHS, api_key="test-placeholder"
        )
        route.assert_called_once()
        explain.assert_called_once()
        assert len(result["table"]) == 10
        assert result["table"].net_sales_aed.max() == pytest.approx(9894417.27)
        assert "AI interpretation" in result["text"]


@pytest.mark.parametrize(
    "issue", ["duplicate", "unmatched", "conflict", "date", "numeric", "uom"]
)
def test_invalid_workbooks_fail_closed(issue):
    sales = pd.DataFrame(
        {
            "Month": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")],
            "Customer": ["C1", "C1"],
            "Country": ["UAE", "UAE"],
            "Customer type": ["Trade", "Trade"],
            "Brand": ["B1", "B1"],
            "Product code": ["P001", "P001"],
            "Division": ["Food", "Food"],
            "Category": ["Cat", "Cat"],
            "Sub-category": ["Sub", "Sub"],
            "UOM": ["EA", "EA"],
            "Quantity": [1, 2],
            "Net sales value (AED)": [10, 20],
            "Cost of sales (AED)": [5, 10],
        }
    )
    products = sales[
        ["Brand", "Product code", "Division", "Category", "Sub-category"]
    ].drop_duplicates()
    customers = pd.DataFrame(
        {
            "Customer": ["C1"],
            "Country": ["UAE"],
            "Customer type": ["Trade"],
            "Sales channel": ["PRIVATE"],
        }
    )
    if issue == "duplicate":
        products = pd.concat([products, products])
    elif issue == "unmatched":
        sales.loc[0, "Product code"] = "P999"
    elif issue == "conflict":
        sales.loc[0, "Brand"] = "B2"
    elif issue == "date":
        sales.loc[0, "Month"] = pd.Timestamp("2025-01-01")
    elif issue == "numeric":
        sales.loc[0, "Quantity"] = float("nan")
    elif issue == "uom":
        sales.loc[0, "UOM"] = "KG"
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, df in [
            ("Sales 2024", sales),
            ("Products", products),
            ("Customers", customers),
            ("About the data", pd.DataFrame({"Description": ["test fixture only"]})),
        ]:
            df.to_excel(writer, sheet_name=name, index=False)
    with pytest.raises(ValueError):
        load_workbook(buffer.getvalue())
