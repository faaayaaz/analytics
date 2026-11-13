"""Optional live Chromium checks for the November planning-workbench release."""

import io
import json
from zipfile import ZipFile

import pandas as pd
from playwright.sync_api import expect, sync_playwright


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(
        viewport={"width": 1536, "height": 1080}, accept_downloads=True
    )
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:8501")
    page.locator('[data-testid="stMetricValue"]').first.wait_for(timeout=90000)

    def period(label):
        page.get_by_role("button", name="Period & reset", exact=False).click()
        page.get_by_role("button", name=label, exact=True).click()
        page.get_by_text(
            "Oct–Dec 2024" if label == "Q4 only" else "Jan–Dec 2024", exact=False
        ).wait_for(timeout=30000)
        page.keyboard.press("Escape")
        page.get_by_role("heading", name="Executive overview", exact=True).click()

    def download(label, path):
        with page.expect_download(timeout=30000) as event:
            page.get_by_role("button", name=label, exact=True).click()
        event.value.save_as(path)
        return path

    period("Q4 only")
    page.get_by_role("button", name="Review tools", exact=False).click()
    page.get_by_text("Compare with previous period", exact=True).click()
    expect(page.locator('[data-testid="stMetricDelta"]').first).to_contain_text(
        "vs Jul–Sep 2024", timeout=30000
    )
    page.get_by_role("button", name="Prepare planning brief", exact=True).click()
    page.get_by_role("button", name="Download planning brief", exact=True).wait_for(
        timeout=30000
    )
    with ZipFile(
        download("Download planning brief", "/tmp/supplyiq_planning_brief.zip")
    ) as archive:
        assert json.loads(archive.read("scope.json"))["period"] == [
            "2024-10",
            "2024-11",
            "2024-12",
        ]
        totals = pd.read_csv(io.BytesIO(archive.read("kpis.csv")))
        assert abs(totals["Net Sales (AED)"].iloc[0] - 113146628.69) < 0.01
    page.keyboard.press("Escape")
    page.get_by_role("heading", name="Executive overview", exact=True).click()
    page.screenshot(path="/tmp/supplyiq-review-overview.png", full_page=False)
    period("Full year")

    page.get_by_text("SKU analysis", exact=True).first.click()
    page.get_by_role("combobox", name="Explore planning segment", exact=True).click()
    page.get_by_role("option", name="AZ", exact=True).click()
    page.get_by_text("14 products · AED", exact=False).wait_for(timeout=30000)
    page.get_by_role("button", name="Use this segment in explorer", exact=True).click()
    page.get_by_text("Showing 14 of 250 SKUs.", exact=False).wait_for(timeout=30000)
    table = pd.read_csv(
        download("Download explorer view", "/tmp/supplyiq_explorer.csv")
    )
    assert len(table) == 14 and set(table.segment) == {"AZ"}
    page.get_by_role(
        "heading", name="SKU explorer", exact=True
    ).scroll_into_view_if_needed()
    page.screenshot(path="/tmp/supplyiq-review-explorer.png", full_page=False)
    page.get_by_role("button", name="Reset explorer", exact=True).click()
    page.get_by_text("Showing 250 of 250 SKUs.", exact=False).wait_for(timeout=30000)

    page.get_by_text("Demand forecasting", exact=True).first.click()
    page.get_by_text("Compare methods and inspect forecast errors", exact=True).click()
    comparison = pd.read_csv(
        download("Download model comparison", "/tmp/supplyiq_model_comparison.csv")
    )
    assert len(comparison) == 4
    assert comparison.groupby("horizon_months").test_origins.nunique().eq(1).all()
    with ZipFile(
        download("Download forecast review pack", "/tmp/supplyiq_forecast_review.zip")
    ) as archive:
        assert len(pd.read_csv(io.BytesIO(archive.read("forecast_estimates.csv")))) == 3
        assumptions = json.loads(archive.read("assumptions.json"))
        assert assumptions["three_step_paths_overlap"] is True
        assert len(assumptions["history_months"]) == 12

    page.locator(".st-key-open_supplyiq button").click()
    dialog = page.get_by_role("dialog")
    dialog.get_by_role("button", name="Top 10 SKUs", exact=True).click()
    dialog.get_by_text("Top 10 products by sales after returns", exact=False).wait_for(
        timeout=30000
    )
    dialog.get_by_role("button", name="Settings", exact=True).click()
    path = download("Download conversation", "/tmp/supplyiq_conversation.md")
    assert "P195" in open(path).read()
    page.keyboard.press("Escape")
    if dialog.is_visible():
        dialog.get_by_role("button", name="Close", exact=True).click()

    page.get_by_text("Data quality & downloads", exact=True).first.click()
    page.get_by_text("Inspect flagged records in your selection", exact=True).click()
    flagged = pd.read_csv(
        download("Download flagged records", "/tmp/supplyiq_flagged.csv")
    )
    assert len(flagged) == 227
    assert flagged.review_reason.str.contains("sign difference").sum() == 11
    assert flagged.review_reason.str.contains("zero quantity").sum() == 216
    assert not errors, errors
    assert page.locator('[data-testid="stException"]').count() == 0
    print(
        "PASS: period deltas, scoped brief ZIP, AZ explorer and CSV, matched-origin model comparison, forecast ZIP, chat transcript, flagged records; no browser errors."
    )
    browser.close()
