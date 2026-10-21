from playwright.sync_api import sync_playwright, expect

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
    page.locator(".js-plotly-plot:visible").nth(2).wait_for(timeout=30000)
    assert page.locator(".js-plotly-plot:visible").count() >= 3
    # Verify the accessible chart-explanation tooltip.
    page.get_by_role("button", name="Help", exact=True).first.hover()
    expect(page.get_by_role("tooltip")).to_contain_text(
        "Sales after returns and credit notes", timeout=10000
    )
    # Exercise real Plotly hover and built-in interaction controls.
    plot = page.locator(".js-plotly-plot").first
    plot.hover()
    page.get_by_role("button", name="Zoom in").first.click()
    page.get_by_role("button", name="Autoscale").first.click()
    plot.locator(".scatterlayer .point").first.hover(force=True)
    assert plot.locator(".hoverlayer").count() == 1
    page.get_by_role("button", name="Explore trend", exact=True).nth(0).click()
    page.get_by_role("heading", name="Net Units Sold", exact=True).wait_for(
        timeout=30000
    )
    page.get_by_text("Line", exact=True).click()
    page.get_by_role("tab", name="Sales breakdown", exact=True).click()
    page.locator(".js-plotly-plot:visible").nth(3).wait_for(timeout=30000)
    page.get_by_role("tab", name="Changes & insights", exact=True).click()
    page.get_by_role("heading", name="Executive insights", exact=True).wait_for(
        timeout=30000
    )
    page.get_by_role("tab", name="Sales & demand", exact=True).click()
    page.get_by_text("SKU analysis", exact=True).first.click()
    page.get_by_text("SKU explorer", exact=True).wait_for(timeout=30000)
    page.get_by_label("Search product, brand or category").fill("P001")
    page.get_by_label("Search product, brand or category").press("Enter")
    grid = page.locator('[data-testid="stDataFrame"]').nth(2)
    # Search is applied on Enter. Wait until the product selector is available after rerun.
    page.get_by_role("combobox", name="Open product demand history").wait_for(
        timeout=30000
    )
    page.wait_for_function(
        "() => {const grids = document.querySelectorAll('[data-testid=stDataFrame]'); const canvas = grids[2]?.querySelector('canvas'); return canvas && canvas.height <= 100;}",
        timeout=30000,
    )
    grid.locator("canvas").first.click(position={"x": 18, "y": 53}, force=True)
    expect(
        page.get_by_role("combobox", name="Open product demand history")
    ).to_have_value("P001", timeout=30000)
    with page.expect_download(timeout=30000) as event:
        page.get_by_role("button", name="Download ABC–XYZ & planning signals").click()
    download = event.value
    download.save_as("/tmp/sku_segmentation.csv")
    import pandas as pd

    table = pd.read_csv("/tmp/sku_segmentation.csv")
    assert len(table) == 250 and abs(table.sales.sum() - 441894325.26) < 0.01
    page.screenshot(path="/tmp/supplyiq-sku.png", full_page=True)
    page.get_by_text("Demand forecasting", exact=True).first.click()
    page.get_by_text("Demand forecasting", exact=True).wait_for(timeout=30000)
    with page.expect_download(timeout=30000) as event:
        page.get_by_role("button", name="Download forecast estimates").click()
    event.value.save_as("/tmp/forecast_estimates.csv")
    forecast = pd.read_csv("/tmp/forecast_estimates.csv")
    assert len(forecast) == 3 and "2025" in forecast.month.iloc[0]
    page.locator(".st-key-open_supplyiq button").click()
    page.get_by_role("button", name="Analyze selected question").wait_for(timeout=30000)
    page.get_by_role("button", name="Analyze selected question").click()
    page.get_by_text("Top 10 products by sales after returns", exact=False).wait_for(
        timeout=30000
    )
    page.get_by_role("button", name="Demand variability", exact=True).click()
    page.get_by_text(
        "Products with the biggest month-to-month swings", exact=False
    ).wait_for(timeout=30000)
    page.get_by_text("Data quality & downloads", exact=True).first.click()
    page.get_by_text("Data quality & totals", exact=True).wait_for(timeout=30000)
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
