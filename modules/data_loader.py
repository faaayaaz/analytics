"""Validated, cardinality-safe workbook ingestion. Workbook text is data, never instructions."""

from io import BytesIO
from pathlib import Path
import pandas as pd

DEFAULT_PATH = (
    Path(__file__).resolve().parents[1] / "data/Assignment_Supply_Planner_Consumer.xlsx"
)
RENAME = {
    "Month": "month",
    "Customer": "customer",
    "Country": "country",
    "Customer type": "customer_type",
    "Brand": "brand",
    "Product code": "product",
    "Division": "division",
    "Category": "category",
    "Sub-category": "subcategory",
    "UOM": "uom",
    "Quantity": "quantity",
    "Net sales value (AED)": "sales",
    "Cost of sales (AED)": "cost",
    "Sales channel": "channel",
}
DIMENSIONS = [
    "division",
    "category",
    "brand",
    "product",
    "customer_type",
    "country",
    "channel",
]
MONTHS = pd.date_range("2024-01-01", periods=12, freq="MS")


def load_workbook(source=DEFAULT_PATH):
    source = BytesIO(source) if isinstance(source, bytes) else source
    sheets = pd.read_excel(source, sheet_name=None)
    required = {"Sales 2024", "Products", "Customers", "About the data"}
    if not required.issubset(sheets):
        raise ValueError("Workbook must contain: " + ", ".join(sorted(required)))
    s, p, c = [
        sheets[k].rename(columns=RENAME).copy()
        for k in ["Sales 2024", "Products", "Customers"]
    ]
    expected = {
        "month",
        "customer",
        "country",
        "customer_type",
        "brand",
        "product",
        "division",
        "category",
        "subcategory",
        "uom",
        "quantity",
        "sales",
        "cost",
    }
    if (
        not expected.issubset(s)
        or not {"product", "brand", "division", "category", "subcategory"}.issubset(p)
        or not {"customer", "country", "customer_type", "channel"}.issubset(c)
    ):
        raise ValueError("Required workbook columns are missing.")
    report = {
        "sales_rows": len(s),
        "product_rows": len(p),
        "customer_rows": len(c),
        "missing_sales_cells": int(s.isna().sum().sum()),
        "exact_duplicate_sales_rows": int(s.duplicated().sum()),
        "duplicate_product_keys": int(p["product"].duplicated().sum()),
        "duplicate_customer_keys": int(c["customer"].duplicated().sum()),
        "missing_product_keys": int(p["product"].isna().sum()),
        "missing_customer_keys": int(c["customer"].isna().sum()),
    }
    if any(
        report[k]
        for k in [
            "duplicate_product_keys",
            "duplicate_customer_keys",
            "missing_product_keys",
            "missing_customer_keys",
        ]
    ):
        raise ValueError(
            "Master keys must be unique and non-null; refusing a potentially multiplying join."
        )
    s["month"] = pd.to_datetime(s["month"], errors="coerce")
    report["invalid_dates"] = int((s.month.isna() | ~s.month.isin(MONTHS)).sum())
    for col in ["quantity", "sales", "cost"]:
        s[col] = pd.to_numeric(s[col], errors="coerce")
        import numpy as np

        if not np.isfinite(s[col]).all():
            raise ValueError(
                f"{col} contains missing, invalid or non-finite values; correct the source before analysis."
            )
    if report["invalid_dates"]:
        raise ValueError(
            "Only first-of-month dates in 2024 are supported by this assessment."
        )
    report["unmatched_products"] = int((~s["product"].isin(p["product"])).sum())
    report["unmatched_customers"] = int((~s["customer"].isin(c["customer"])).sum())
    if report["unmatched_products"] or report["unmatched_customers"]:
        raise ValueError("Unmatched master keys: correct the workbook before analysis.")
    for master, key, fields in [
        (p, "product", ["brand", "division", "category", "subcategory"]),
        (c, "customer", ["country", "customer_type"]),
    ]:
        j = s.merge(
            master[[key] + fields],
            on=key,
            how="left",
            validate="many_to_one",
            suffixes=("", "_master"),
        )
        for field in fields:
            report[f"{field}_master_mismatches"] = int(
                j[field]
                .fillna("<missing>")
                .ne(j[field + "_master"].fillna("<missing>"))
                .sum()
            )
    if any(v for k, v in report.items() if k.endswith("_master_mismatches")):
        raise ValueError(
            "Sales attributes conflict with master data; resolve the conflicting records before analysis."
        )
    result = s.merge(
        c[["customer", "channel"]], on="customer", how="left", validate="many_to_one"
    )
    if result["uom"].isna().any() or result["uom"].nunique() != 1:
        raise ValueError(
            "A single, non-null UOM is required for aggregated demand. Split mixed units before analysis."
        )
    report["missing_master_cells"] = int(p.isna().sum().sum() + c.isna().sum().sum())
    report["months_present"] = int(s.month.nunique())
    report["negative_quantity_rows"] = int((s.quantity < 0).sum())
    report["sign_mismatch_rows"] = int(
        ((s.quantity * s.sales < 0) | (s.quantity * s.cost < 0)).sum()
    )
    report["zero_quantity_rows"] = int((s.quantity == 0).sum())
    report["uom"] = str(s.uom.iloc[0]) if len(s) else "N/A"
    report["workbook_sales"] = float(s.sales.sum())
    report["workbook_cost"] = float(s.cost.sum())
    report["workbook_quantity"] = float(s.quantity.sum())
    report["reconciled"] = len(result) == len(s) and all(
        abs(result[k].sum() - s[k].sum()) < 0.001 for k in ["sales", "cost", "quantity"]
    )
    about = sheets["About the data"]
    report["about"] = "\n".join(
        [str(x) for x in about.columns]
        + [str(v) for v in about.to_numpy().flatten() if pd.notna(v)]
    )
    for col in DIMENSIONS + ["customer", "subcategory", "uom"]:
        result[col] = result[col].fillna("Unknown").astype(str)
    return result, report


def filter_data(data, selections, months):
    mask = data.month.isin(months)
    for col, values in selections.items():
        mask &= data[col].isin(values)
    return data.loc[mask].copy()
