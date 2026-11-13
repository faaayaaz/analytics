"""Source-safe edge cases for ingestion, scope and undefined calculations."""

from io import BytesIO
import numpy as np
import pandas as pd
import pytest
from modules.data_loader import load_workbook, MONTHS
from modules.kpi_calculations import kpis, monthly_demand, ratio, executive_insights


def source_frames():
    sales = pd.DataFrame(
        {
            "Month": pd.to_datetime(["2024-01-01", "2024-03-01"]),
            "Customer": ["Customer A", "Customer A"],
            "Country": ["UAE", "UAE"],
            "Customer type": ["Trade", "Trade"],
            "Brand": ["Brand 1", "Brand 1"],
            "Product code": ["P001", "P001"],
            "Division": ["Food", "Food"],
            "Category": ["Category A", "Category A"],
            "Sub-category": ["Sub A", "Sub A"],
            "UOM": ["EA", "EA"],
            "Quantity": [100, 120],
            "Net sales value (AED)": [1000.0, 1200.0],
            "Cost of sales (AED)": [600.0, 720.0],
        }
    )
    products = sales[
        ["Brand", "Product code", "Division", "Category", "Sub-category"]
    ].drop_duplicates()
    customers = (
        sales[["Customer", "Country", "Customer type"]]
        .drop_duplicates()
        .assign(**{"Sales channel": "PRIVATE"})
    )
    return sales, products, customers


def workbook_bytes(sales, products, customers):
    content = BytesIO()
    with pd.ExcelWriter(content, engine="openpyxl") as writer:
        for name, frame in [
            ("Sales 2024", sales),
            ("Products", products),
            ("Customers", customers),
            ("About the data", pd.DataFrame({"Source": ["Test fixture only"]})),
        ]:
            frame.to_excel(writer, sheet_name=name, index=False)
    return content.getvalue()


@pytest.mark.parametrize(
    "place",
    ["sale_product", "sale_customer", "master_product", "master_customer", "uom"],
)
def test_whitespace_only_keys_and_units_are_rejected(place):
    sales, products, customers = source_frames()
    if place == "sale_product":
        sales.loc[0, "Product code"] = "  "
    if place == "sale_customer":
        sales.loc[0, "Customer"] = "\t "
    if place == "master_product":
        products.loc[products.index[0], "Product code"] = "  "
    if place == "master_customer":
        customers.loc[customers.index[0], "Customer"] = "  "
    if place == "uom":
        sales["UOM"] = "  "
    with pytest.raises(ValueError):
        load_workbook(workbook_bytes(sales, products, customers))


def test_corrupt_file_has_safe_actionable_message():
    with pytest.raises(ValueError, match="valid, unencrypted .xlsx") as error:
        load_workbook(b"Not an Excel archive; untrusted internal detail")
    assert "untrusted internal detail" not in str(error.value)


def test_ambiguous_headers_and_empty_sheets_fail_closed():
    sales, products, customers = source_frames()
    sales = pd.concat([sales, sales[["Quantity"]]], axis=1)
    with pytest.raises(ValueError, match="repeated"):
        load_workbook(workbook_bytes(sales, products, customers))
    sales, products, customers = source_frames()
    with pytest.raises(ValueError, match="at least one record"):
        load_workbook(workbook_bytes(sales.iloc[:0], products, customers))


def test_boolean_quantities_are_not_interpreted_as_units():
    sales, products, customers = source_frames()
    sales["Quantity"] = [True, False]
    with pytest.raises(ValueError, match="true/false"):
        load_workbook(workbook_bytes(sales, products, customers))


def test_blank_optional_channels_are_reported_as_unknown():
    sales, products, customers = source_frames()
    customers["Sales channel"] = "   "
    data, report = load_workbook(workbook_bytes(sales, products, customers))
    assert set(data.channel) == {"Unknown"}
    assert report["missing_master_cells"] == 1
    assert report["reconciled"]
    assert "2024-02" in report["missing_calendar_months"]
    assert data.sales.sum() == 2200


def test_monthly_growth_respects_calendar_gaps_and_scope():
    data, _ = load_workbook(workbook_bytes(*source_frames()))
    selected = [MONTHS[2], MONTHS[0], MONTHS[2]]
    monthly = monthly_demand(data, selected)
    assert monthly.month.tolist() == [MONTHS[0], MONTHS[2]]
    assert monthly.growth_pct.isna().all()
    assert np.isnan(kpis(data, selected)["MoM Demand Growth %"])
    assert kpis(data, [MONTHS[0]])["Net Sales (AED)"] == 1000
    assert kpis(data, [])["Active SKUs"] == 0
    assert executive_insights(data, [MONTHS[1]]) == [
        "No records match the selected filters."
    ]


def test_monthly_zero_sales_are_retained_without_invented_growth():
    data, _ = load_workbook(workbook_bytes(*source_frames()))
    monthly = monthly_demand(data, MONTHS[:3])
    assert monthly.quantity.tolist() == [100, 0, 120]
    assert monthly.growth_pct.iloc[1] == -100
    assert np.isnan(monthly.growth_pct.iloc[2])


@pytest.mark.parametrize(
    "n,d", [(np.inf, 1), (1, np.inf), (np.nan, 1), (1, 0), (None, 1), (1, "bad")]
)
def test_ratio_nonfinite_inputs_are_na(n, d):
    assert np.isnan(ratio(n, d))


def test_signed_margin_still_works_and_undefined_insights_are_readable():
    data, _ = load_workbook(workbook_bytes(*source_frames()))
    negative = data.copy()
    negative[["sales", "cost", "quantity"]] = -negative[["sales", "cost", "quantity"]]
    assert kpis(negative, MONTHS)["Gross Margin %"] == pytest.approx(40)
    narrative = " ".join(executive_insights(negative, MONTHS))
    assert "nan%" not in narrative.lower()
    assert "N/A" in narrative


def test_finite_cells_with_overflowing_totals_are_rejected():
    sales, products, customers = source_frames()
    sales["Net sales value (AED)"] = [1e308, 1e308]
    with pytest.raises(ValueError, match="non-finite"):
        load_workbook(workbook_bytes(sales, products, customers))
