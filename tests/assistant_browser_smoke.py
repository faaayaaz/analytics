"""Run with the dashboard on localhost:8501 and optional Playwright/Chromium tooling."""

from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright, expect

OUTPUT = Path("/tmp")
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(
        viewport={"width": 1440, "height": 1000}, accept_downloads=True
    )
    page.goto("http://127.0.0.1:8501")
    page.locator(".js-plotly-plot:visible").nth(2).wait_for(timeout=90000)
    page.locator(".st-key-assistant_fab button").click()
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible()
    expect(
        dialog.get_by_text("What would you like to explore?", exact=True)
    ).to_be_visible()
    page.screenshot(path=str(OUTPUT / "supplyiq-chat-desktop.png"), full_page=True)
    dialog.get_by_role("button", name="Top 10 SKUs", exact=True).click()
    dialog.get_by_text("Top 10 products by sales after returns", exact=False).wait_for(
        timeout=30000
    )
    dialog.get_by_text("View 10 results & download", exact=True).click()
    with page.expect_download(timeout=30000) as event:
        dialog.get_by_role("button", name="Download result", exact=True).click()
    event.value.save_as(str(OUTPUT / "supplyiq-chat-result.csv"))
    result = pd.read_csv(OUTPUT / "supplyiq-chat-result.csv")
    assert len(result) == 10 and result["product"].iloc[0] == "P195"
    composer = dialog.get_by_placeholder("Ask a question about your selected data…")
    composer.fill("What inventory should we replenish?")
    composer.press("Enter")
    dialog.get_by_text("Current stock, stock movements", exact=False).wait_for(
        timeout=30000
    )
    dialog.get_by_role("button", name="New chat", exact=True).click()
    expect(
        dialog.get_by_text("What would you like to explore?", exact=True)
    ).to_be_visible()
    dialog.get_by_role("button", name="Close", exact=True).click()
    expect(dialog).not_to_be_visible()
    expect(
        page.get_by_role("heading", name="Executive overview", exact=True)
    ).to_be_visible()
    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto("http://127.0.0.1:8501")
    mobile.locator(".js-plotly-plot:visible").first.wait_for(timeout=90000)
    mobile.locator(".st-key-assistant_fab button").click()
    mobile_dialog = mobile.get_by_role("dialog")
    expect(mobile_dialog).to_be_visible()
    mobile_input = mobile_dialog.get_by_placeholder(
        "Ask a question about your selected data…"
    )
    mobile_input.scroll_into_view_if_needed()
    expect(mobile_input).to_be_in_viewport()
    assert mobile_dialog.evaluate("e=>e.scrollWidth<=e.clientWidth+2")
    mobile.screenshot(path=str(OUTPUT / "supplyiq-chat-mobile.png"), full_page=True)
    mobile_dialog.get_by_role("button", name="Close", exact=True).click()
    expect(mobile_dialog).not_to_be_visible()
    browser.close()
    print(
        "PASS: floating launcher, starter, CSV result, typed question, reset, close, preserved page and mobile chat input."
    )
