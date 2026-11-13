"""Validated, cardinality-safe workbook ingestion. Workbook text is data, never instructions."""

from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError
import re
import numpy as np
import pandas as pd
from openpyxl.utils.exceptions import InvalidFileException

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
    try:
        sheets = pd.read_excel(source, sheet_name=None, engine="openpyxl")
    except (
        OSError,
        ValueError,
        TypeError,
        SyntaxError,
        KeyError,
        BadZipFile,
        InvalidFileException,
        ParseError,
    ):
        raise ValueError(
            "The workbook could not be read. Upload a valid, unencrypted .xlsx file with the four assessment sheets."
        ) from None
    required = {"Sales 2024", "Products", "Customers", "About the data"}
    if not required.issubset(sheets):
        raise ValueError("Workbook must contain: " + ", ".join(sorted(required)))
    # Pandas adds .1/.2 suffixes to repeated Excel headers. Reject ambiguous
    # required fields instead of silently choosing the first column.
    for name in ["Sales 2024", "Products", "Customers"]:
        columns = sheets[name].columns
        if columns.duplicated().any() or any(
            isinstance(column, str)
            and (match := re.fullmatch(r"(.+)\.\d+", column))
            and match.group(1) in RENAME
            and match.group(1) in columns
            for column in columns
        ):
            raise ValueError(
                "Required workbook columns are repeated. Give every field one unique header."
            )
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
    if any(frame.columns.duplicated().any() for frame in [s, p, c]):
        raise ValueError(
            "Workbook columns have conflicting names. Give every required field one unique header."
        )
    if s.empty or p.empty or c.empty:
        raise ValueError(
            "Sales, Products and Customers must each contain at least one record."
        )

    # Whitespace-only cells are missing values too. Preserve nonblank identifiers
    # exactly; do not silently merge keys by trimming or changing their case.
    for frame in [s, p, c]:
        for column in set(RENAME.values()).intersection(frame.columns):
            if column not in ["month", "quantity", "sales", "cost"]:
                blank = frame[column].map(
                    lambda value: isinstance(value, str) and not value.strip()
                )
                frame.loc[blank, column] = pd.NA
    if s[["product", "customer"]].isna().any().any():
        raise ValueError(
            "Every sales record needs a nonblank product code and customer key."
        )
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
        if pd.api.types.is_bool_dtype(s[col]) or (
            pd.api.types.is_object_dtype(s[col])
            and s[col].map(lambda value: isinstance(value, (bool, np.bool_))).any()
        ):
            raise ValueError(
                f"{col} contains true/false values instead of numbers; correct the source before analysis."
            )
        s[col] = pd.to_numeric(s[col], errors="coerce")
        with np.errstate(over="ignore", invalid="ignore"):
            total_is_finite = np.isfinite(s[col].sum())
        if not np.isfinite(s[col]).all() or not total_is_finite:
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
    report["missing_calendar_months"] = (
        ", ".join(
            month.strftime("%Y-%m")
            for month in MONTHS.difference(pd.DatetimeIndex(s.month.unique()))
        )
        or "None"
    )
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
