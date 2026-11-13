import io
import json
from zipfile import ZipFile
import pandas as pd
import pytest
from modules.data_loader import load_workbook, MONTHS
from modules.period_comparison import compare_period
from modules.reporting import planning_brief, review_records


@pytest.fixture(scope="module")
def sales():
    return load_workbook()[0]


def test_comparison_uses_matching_earlier_months_and_same_dimension(sales):
    food = sales.loc[sales.division == "Food"]
    comparison = compare_period(food, MONTHS[9:])
    assert comparison["available"]
    assert comparison["previous_months"] == list(MONTHS[6:9])
    now = food.loc[food.month.isin(MONTHS[9:])]
    previous = food.loc[food.month.isin(MONTHS[6:9])]
    assert comparison["current"]["Net Sales (AED)"] == pytest.approx(now.sales.sum())
    assert comparison["previous"]["Net Sales (AED)"] == pytest.approx(
        previous.sales.sum()
    )
    assert comparison["deltas"]["Net Units Sold"] == pytest.approx(
        (now.quantity.sum() - previous.quantity.sum()) / previous.quantity.sum() * 100
    )
    now_margin = (now.sales.sum() - now.cost.sum()) / now.sales.sum() * 100
    previous_margin = (
        (previous.sales.sum() - previous.cost.sum()) / previous.sales.sum() * 100
    )
    assert comparison["deltas"]["Gross Margin %"] == pytest.approx(
        now_margin - previous_margin
    )
    assert not compare_period(food, MONTHS)["available"]
    assert not compare_period(food, [MONTHS[6], MONTHS[8]])["available"]
    assert not compare_period(food, MONTHS[9:], MONTHS.delete(7))["available"]
    assert compare_period(food, MONTHS[9:], MONTHS)["available"]


def test_brief_reconciles_with_selected_rows_and_records_thresholds(sales):
    subset = sales.loc[(sales.division == "Food") & sales.month.isin(MONTHS[9:])]
    with ZipFile(
        io.BytesIO(planning_brief(subset, MONTHS[9:], (75, 90, 0.4, 0.8)))
    ) as archive:
        scope = json.loads(archive.read("scope.json"))
        assert scope["transactions"] == len(subset)
        assert scope["period"] == ["2024-10", "2024-11", "2024-12"]
        assert scope["filters_observed"]["division"] == ["Food"]
        assert scope["classification_thresholds"]["a_pct"] == 75
        k = pd.read_csv(io.BytesIO(archive.read("kpis.csv")))
        m = pd.read_csv(io.BytesIO(archive.read("monthly_performance.csv")))
        s = pd.read_csv(io.BytesIO(archive.read("sku_segmentation.csv")))
        assert k["Net Sales (AED)"].iloc[0] == pytest.approx(subset.sales.sum())
        assert m.sales.sum() == pytest.approx(subset.sales.sum())
        assert s.sales.sum() == pytest.approx(subset.sales.sum())
        assert "no stock" in archive.read("planning_brief.md").decode()


def test_review_flags_are_evidence_not_all_negative_transactions():
    rows = pd.DataFrame(
        {
            "quantity": [1, -1, -1, 0, 1],
            "sales": [10, -10, 10, 5, 10],
            "cost": [5, -5, -5, 0, 5],
        }
    )
    flagged = review_records(rows)
    assert set(flagged.index) == {0, 2, 3, 4}
    assert "sign difference" in flagged.loc[2, "review_reason"]
    assert "zero quantity" in flagged.loc[3, "review_reason"]
    assert "repeated" in flagged.loc[0, "review_reason"]
    assert 1 not in flagged.index
