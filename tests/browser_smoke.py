from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(
        viewport={"width": 1536, "height": 1080}, accept_downloads=True
    )
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:8501")
    page.get_by_text("Executive overview", exact=True).last.wait_for(timeout=90000)
    page.locator('[data-testid="stMetricValue"]').first.wait_for(timeout=90000)
    page.screenshot(path="/tmp/supplyiq-overview.png", full_page=True)
    assert page.locator(".js-plotly-plot").count() >= 7
    # Exercise real Plotly hover and built-in interaction controls.
    plot = page.locator(".js-plotly-plot").first
    plot.hover()
    page.get_by_role("button", name="Zoom in").first.click()
    page.get_by_role("button", name="Autoscale").first.click()
    plot.locator(".scatterlayer .point").first.hover(force=True)
    assert plot.locator(".hoverlayer").count() == 1
    page.get_by_text("SKU & demand intelligence", exact=True).first.click()
    page.get_by_text("SKU planning workbench", exact=True).wait_for(timeout=30000)
    page.get_by_label("Search product, brand or category").fill("P001")
    page.get_by_label("Search product, brand or category").press("Enter")
    with page.expect_download(timeout=30000) as event:
        page.get_by_role("button", name="Download ABC–XYZ & planning signals").click()
    download = event.value
    download.save_as("/tmp/sku_segmentation.csv")
    import pandas as pd

    table = pd.read_csv("/tmp/sku_segmentation.csv")
    assert len(table) == 250 and abs(table.sales.sum() - 441894325.26) < 0.01
    page.screenshot(path="/tmp/supplyiq-sku.png", full_page=True)
    page.get_by_text("Forecasting & scenario lab", exact=True).first.click()
    page.get_by_text("Demand forecasting & scenario lab", exact=True).wait_for(
        timeout=30000
    )
    with page.expect_download(timeout=30000) as event:
        page.get_by_role("button", name="Download forecast estimates").click()
    event.value.save_as("/tmp/forecast_estimates.csv")
    forecast = pd.read_csv("/tmp/forecast_estimates.csv")
    assert len(forecast) == 3 and "2025" in forecast.month.iloc[0]
    page.get_by_text("SupplyIQ assistant", exact=True).first.click()
    page.get_by_role("button", name="Analyze selected question").wait_for(timeout=30000)
    page.get_by_role("button", name="Analyze selected question").click()
    page.get_by_text("Top 10 SKUs by signed net sales", exact=False).wait_for(
        timeout=30000
    )
    page.get_by_text("Data quality & exports", exact=True).first.click()
    page.get_by_text("Data quality & reconciliation", exact=True).wait_for(
        timeout=30000
    )
    with page.expect_download(timeout=30000) as event:
        page.get_by_role("button", name="Download filtered transactions").click()
    event.value.save_as("/tmp/filtered_sales.csv")
    exported = pd.read_csv("/tmp/filtered_sales.csv")
    assert len(exported) == 160572 and exported.quantity.sum() == 22323030
    assert abs(exported.sales.sum() - 441894325.26) < 0.01
    assert not errors, errors
    # Confirm layout is usable at a narrow viewport.
    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto("http://127.0.0.1:8501")
    mobile.locator('[data-testid="stMetricValue"]').first.wait_for(timeout=90000)
    # Streamlit auto-collapses the sidebar on a fresh narrow-screen session.
    assert mobile.locator('[data-testid="stMain"]').evaluate(
        "e => e.scrollWidth <= e.clientWidth + 2"
    )
    mobile.screenshot(path="/tmp/supplyiq-mobile.png", full_page=True)
    print(
        "PASS: five pages, Plotly zoom/autoscale/hover, assistant execution, CSV downloads and mobile render; no browser errors."
    )
    browser.close()
