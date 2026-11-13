"""Portable, locally generated planning brief. No external publishing or API calls."""

import io
import json
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime, timezone
import pandas as pd
from .kpi_calculations import kpis, monthly_demand, executive_insights
from .abc_xyz_analysis import classify


def planning_brief(data, months, thresholds=(80, 95, 0.5, 1)):
    months = pd.DatetimeIndex(sorted(set(pd.to_datetime(months))))
    data = data.loc[data.month.isin(months)]
    metrics = kpis(data, months)
    clean = {
        name: None if pd.isna(value) else float(value)
        for name, value in metrics.items()
    }
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "period": [pd.Timestamp(month).strftime("%Y-%m") for month in sorted(months)],
        "transactions": len(data),
        "products": int(data["product"].nunique()),
        "currency": "AED",
        "unit": str(data.uom.iloc[0]) if len(data) else None,
        "classification_thresholds": dict(
            zip(["a_pct", "b_cumulative_pct", "x_cv", "y_cv"], thresholds)
        ),
        "filters_observed": {
            col: sorted(data[col].dropna().astype(str).unique().tolist())
            for col in [
                "division",
                "category",
                "brand",
                "product",
                "customer_type",
                "country",
                "channel",
            ]
            if col in data
        },
        "limitations": [
            "Selected sales history, including returns/credits; no stock, lead-time or purchase-order data.",
            "Average monthly net demand is selected units divided by 12.",
            "Observed filter values list records present in this extract, not excluded zero-sale records.",
        ],
    }
    lines = [
        "# SupplyIQ — Planning brief",
        "",
        "Selected period: " + ", ".join(manifest["period"]),
        "",
        "## Key figures",
    ]
    lines += [
        f"- {name}: " + ("N/A" if value is None else f"{value:,.2f}")
        for name, value in clean.items()
    ]
    lines += [
        "",
        "## Calculated observations",
        *["- " + text for text in executive_insights(data, months)],
        "",
        "## Limits",
        *["- " + text for text in manifest["limitations"]],
    ]
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("planning_brief.md", "\n".join(lines))
        archive.writestr(
            "scope.json",
            json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False),
        )
        archive.writestr("kpis.csv", pd.DataFrame([clean]).to_csv(index=False))
        archive.writestr(
            "monthly_performance.csv",
            monthly_demand(data, sorted(months)).to_csv(index=False),
        )
        archive.writestr(
            "sku_segmentation.csv",
            classify(data, months, *thresholds).to_csv(index=False),
        )
    return buffer.getvalue()


def review_records(data):
    """Flag review candidates without deleting rows or claiming every flag is an error."""
    reasons = pd.Series("", index=data.index, dtype=object)
    sign = (data.quantity * data.sales < 0) | (data.quantity * data.cost < 0)
    duplicates = data.duplicated(keep=False)
    adjustment = (data.quantity == 0) & ((data.sales != 0) | (data.cost != 0))
    for mask, label in [
        (sign, "Quantity/financial sign difference"),
        (duplicates, "Exact repeated record"),
        (adjustment, "Value with zero quantity"),
    ]:
        reasons.loc[mask] = (
            reasons.loc[mask].map(lambda value: value + "; " if value else "") + label
        )
    result = data.loc[reasons.ne("")].copy()
    result["review_reason"] = reasons.loc[result.index]
    return result
