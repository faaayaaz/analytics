"""Regression cases for question focus, dashboard-consistent ABC and safe analysis routing."""

from unittest.mock import patch
import pandas as pd
import pytest
from modules.ai_assistant import answer, recognize, segment_in
from modules.assistant_ui import conversation_markdown
from modules.abc_xyz_analysis import classify
from modules.data_loader import MONTHS


@pytest.fixture
def sales():
    rows = []
    specs = [
        ("P001", "Brand 1", "Food", "Snacks", 1000, 1),
        ("P002", "Brand 2", "Personal Care", "Oral Care", 500, 2),
        ("P003", "Brand 10", "Food", "Snacks", 200, 3),
        ("P004", "Brand 3", "Home Care", "Pet Food", 70, 4),
        ("P005", "Brand 10", "Food", "Snacks", 30, 20),
    ]
    for sku, brand, division, category, value, quantity in specs:
        included = MONTHS[[0, 11]] if sku == "P004" else MONTHS
        for month in included:
            rows.append(
                dict(
                    product=sku,
                    brand=brand,
                    division=division,
                    category=category,
                    month=month,
                    sales=value / len(included),
                    quantity=quantity,
                    cost=value / len(included) * 0.5,
                )
            )
    return pd.DataFrame(rows)


def test_preposition_by_is_not_a_segment():
    assert segment_in("Top 10 products by category") is None
    assert recognize("Top 10 products by category") == "top"
    assert segment_in("Show the BY products") == "BY"
    assert segment_in("Which products belong to the by category?") == "BY"


def test_named_brand_preserves_dashboard_segmentation(sales):
    expected = classify(sales)
    for segment in ["BX", "CX"]:
        result = answer(f"Show {segment} products for Brand 10", sales, MONTHS)
        target = expected.loc[
            (expected.brand == "Brand 10") & (expected.segment == segment)
        ]
        assert set(result["table"]["product"]) == set(target["product"])
        assert "all products in the dashboard selection" in result["text"]
    assert answer("Explain product p003", sales, MONTHS)["context"]["product"] == "P003"


def test_new_entity_replaces_old_and_monthly_followup_keeps_focus(sales):
    first = answer("Explain product P001", sales, MONTHS)
    changed = answer("What about Brand   10?", sales, MONTHS, previous=first["context"])
    assert changed["context"].get("brand") == "Brand 10"
    assert "product" not in changed["context"]
    assert changed["table"].quantity.sum() == 276
    follow = answer(
        "Show monthly demand growth", sales, MONTHS, previous=changed["context"]
    )
    assert follow["table"].quantity.sum() == 276
    assert follow["scope_note"] == "Brand 10"
    reset = answer(
        "Show monthly demand for all brands", sales, MONTHS, previous=follow["context"]
    )
    assert "brand" not in reset["context"]
    assert reset["table"].quantity.sum() == sales.quantity.sum()


def test_top_units_and_limit_followups(sales):
    result = answer("Top 2 SKUs by units", sales, MONTHS)
    assert result["table"]["product"].tolist() == ["P005", "P003"]
    assert result["chart"] == ("bar", "product", "net_units")
    follow = answer("What about Brand 10?", sales, MONTHS, previous=result["context"])
    assert follow["context"]["limit"] == 2 and follow["context"]["rank_by"] == "units"
    assert follow["table"]["product"].tolist() == ["P005", "P003"]
    unsupported = answer("Top 3 products by profit", sales, MONTHS)
    assert (
        unsupported["table"] is None and "profitability ranking" in unsupported["text"]
    )


def test_comparisons_include_zero_months_and_named_dimensions(sales):
    compared = answer("Compare P004 and P005 demand history", sales, MONTHS)
    assert compared["context"]["intent"] == "compare"
    assert len(compared["table"]) == 24
    assert (
        compared["table"]
        .loc[
            (compared["table"]["product"] == "P004")
            & (compared["table"].month == MONTHS[1]),
            "net_units",
        ]
        .iloc[0]
        == 0
    )
    division = answer("Compare Food and Personal Care demand", sales, MONTHS)
    assert set(division["table"].division) == {"Food", "Personal Care"}
    category = answer("Summarize Pet Food", sales, MONTHS)
    assert category["context"]["category"] == ["Pet Food"]
    assert (
        "division" not in category["context"]
    )  # Food inside Pet Food is not a division request.


def test_direct_queries_cannot_use_excluded_months_or_model_override(sales):
    unavailable = answer("Top 10 SKUs in 2025", sales, MONTHS)
    assert (
        unavailable["table"] is None and "2025 is not available" in unavailable["text"]
    )
    result = answer("Top 10 SKUs", sales, MONTHS[:1])
    assert result["table"].net_sales_aed.sum() == pytest.approx(
        sales.loc[sales.month == MONTHS[0], "sales"].sum()
    )
    with (
        patch("modules.ai_assistant.llm_route", return_value="summary"),
        patch(
            "modules.ai_assistant.explain_verified",
            return_value="Check your customer mix.",
        ),
    ):
        result = answer(
            "Show BX products for Brand 10", sales, MONTHS, api_key="fake-key"
        )
        assert result["context"]["intent"] == "segment"
        assert set(result["table"]["product"]) == {"P003"}


def test_transcript_exports_only_visible_content_and_redacts_keys():
    secret = "sk-" + ("x" * 30)
    messages = [
        {"role": "system", "text": "Hidden provider system prompt"},
        {"role": "user", "text": "API_KEY=" + secret},
        {
            "role": "assistant",
            "text": "Checked 3 products.",
            "scope_note": "Brand 10",
            "table": pd.DataFrame({"product": ["P003"], "sales": [200]}),
            "api_key": "never-export-this",
        },
    ]
    output = conversation_markdown(messages)
    assert secret not in output and "never-export-this" not in output
    assert "Hidden provider system prompt" not in output
    assert "Brand 10" in output and "P003,200" in output


def test_explicit_sales_followup_replaces_units_ranking(sales):
    first = answer("Top 2 SKUs by units", sales, MONTHS)
    changed = answer("And by sales?", sales, MONTHS, previous=first["context"])
    assert changed["context"]["rank_by"] == "sales"
    assert changed["context"]["limit"] == 2
    assert changed["table"]["product"].tolist() == ["P001", "P002"]
    brand = answer(
        "What about Brand 10 by sales?", sales, MONTHS, previous=first["context"]
    )
    assert brand["table"]["product"].tolist() == ["P003", "P005"]


def test_filtered_out_known_entity_never_silently_uses_other_data(sales):
    scoped = sales.loc[sales.division.eq("Personal Care")].copy()
    scoped.attrs["entity_catalog"] = {
        column: sales[column].unique().tolist()
        for column in ["product", "brand", "division", "category"]
    }
    for question in [
        "Summarize Food",
        "Compare Food and Personal Care",
        "Summarize Snacks",
    ]:
        result = answer(question, scoped, MONTHS)
        assert result["table"] is None
        assert "absent from the current filtered selection" in result["text"]


@pytest.mark.parametrize(
    "question,dimension,expected",
    [
        ("Compare Brand 1 and Brand 10", "brand", {"Brand 1", "Brand 10"}),
        ("Compare Snacks and Oral Care", "category", {"Snacks", "Oral Care"}),
    ],
)
def test_requested_comparison_dimension_is_preserved(
    sales, question, dimension, expected
):
    result = answer(question, sales, MONTHS)
    assert result["context"]["comparison_dimension"] == dimension
    assert set(result["table"][dimension]) == expected
    assert len(result["table"]) == 24
    assert (
        result["table"].net_units.sum()
        == sales.loc[sales[dimension].isin(expected)].quantity.sum()
    )


@pytest.mark.parametrize(
    "question",
    [
        "Top 10 SKUs 2025",
        "Top10 SKUs2025",
        "Summarize 2023",
        "Show sales 2024 versus 2025",
    ],
)
def test_unsupported_years_rejected_in_compact_wording(sales, question):
    result = answer(question, sales, MONTHS)
    assert result["table"] is None
    assert "is not available" in result["text"]
