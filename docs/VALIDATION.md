# Validation record

Validated in the supplied Linux cloud environment on Python 3.12 using the actual assessment workbook. Direct package versions are recorded in `requirements.lock.txt`.

## Automated suite

`python -m pytest -q`: **27 passed**, including:

- Workbook totals independently asserted against the original source: 160,572 sales rows, 250 products, 292 customers; AED 441,894,325.26 sales; AED 334,029,937.73 cost; 22,323,030 EA.
- One-to-many master rejection, unmatched references, attribute conflicts, invalid dates/numerics and mixed-unit fail-closed ingestion.
- Gross profit, positive and negative revenue margin, undefined denominators, negative quantity ratio and nonconsecutive-month growth handling.
- Eligible ABC contribution sums, boundary allocation, nonpositive revenue/mean, population CV and zero-filled included months.
- Strict rolling backtest calculations, MAE/WAPE/bias, zero-demand denominators, exponential smoothing initialization, scenario multiplication and missing/nonconsecutive month rejection.
- All required example assistant intents, results compared with independent Pandas aggregation, global filter restrictions, multi-turn brand follow-up, unknown entities, SQL-like unsupported requests, mocked optional LLM routing/interpretation and simulated API failure fallback.
- Streamlit AppTest navigation through all five pages, KPI results, SKU search, forecast method/scenario changes, local chat execution, Food filtering and empty-month behavior.

## Live application and browser checks

The application was started using `python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501`. The health endpoint returned `ok`. A Chromium/Playwright smoke run exercised:

- Rendered navigation through all five workspaces with no JavaScript page errors.
- Interactive Plotly zoom, autoscale and hover actions.
- SKU search and real local assistant query execution.
- Download buttons for segmentation (250 rows), three-month forecasts and transactions (160,572 rows).
- Downloaded sales and quantity totals reconciled to the source workbook.
- A fresh 390-pixel mobile session rendered the executive page with no main-content horizontal overflow. Screenshots were inspected for desktop and mobile layouts.

To repeat browser validation with the app running, install optional developer tooling `pip install playwright`, provide Chromium at `/usr/bin/chromium`, and run `python tests/browser_smoke.py`. This tooling is not required by the application. The script records screenshots and export files under `/tmp`.

## Limits of validation

No paid API credentials were available: live LLM authentication/provider responses have not been validated. Optional routing and interpretation were tested with mocks and provider failure with a simulated exception. The keyless analytical assistant was run against real workbook data in unit tests, Streamlit AppTest and Chromium.

Streamlit Community Cloud publication has not been performed. No user-facing public URL, authentication layer, real-time operational data feed, inventory integration, supplier integration or 2025 actual-demand validation is included or implied. The workbook's 11 quantity/financial sign differences are preserved and reported, not corrected by assumption.

## Usability update regression

The original version was preserved remotely as `dashboard-v1-original` at `c7d5a45` before editing. After the usability update, the full automated suite reports **28 passed**. The additional interaction test verifies Q4 selection, cascading-filter recovery when changing divisions, full filter reset, guided navigation, +20%/baseline scenario buttons and empty-scope recovery. The five-page Chromium smoke test, Plotly interactions and downloads also pass against the updated app. A real click on the searched P001 workbench row was verified to select P001 in the demand-history control.

## Visual UI refresh

The version before the visual refresh is preserved remotely as `dashboard-v2-before-ui`. The updated suite reports **29 passed**, including an additional test for interactive KPI focus and tab presence. Chromium checks additionally click a KPI trend action, switch the main chart to Line, open Business mix and Growth & insights tabs, and then exercise the existing five-page, SKU selection and download workflow. Desktop and 390-pixel mobile layouts render without main-content horizontal overflow. Source totals and analytical definitions are unchanged.

## Hover-help update

The automated suite reports **31 passed**, adding checks for chart-specific guidance, chart-help descriptions, matrix value tooltips and plain-language axis units. The live Chromium smoke test also hovers over the chart-caption help icon and checks that the selected KPI's explanation appears before exercising chart controls, tabs, SKU selection and downloads.

## Plain-language update

The full automated suite reports **31 passed** after simplifying the wording. Table headings and review messages are translated for display without changing the underlying classification codes, calculations or CSV column identifiers. Browser checks cover the renamed scenario buttons, simpler assistant output, chart help and Data checks & totals page, as well as the existing filter, SKU selection and download interactions.

## Technical-label clarification

Original KPI names, graph-axis labels, table column identifiers, forecast error names and control labels are restored. Plain-language explanations, hover help, recommendations and the glossary remain. Calculations and downloaded data are unchanged. The regression tests verify the original KPI heading and scenario labels alongside the simpler explanation tooltips.

## SupplyIQ interaction buttons

The full suite reports **32 passed**. A new Streamlit interaction test opens a summary from a Food-filtered dashboard, verifies the AED 193,130,712.74 result, runs a quick top-SKU question and monthly-demand follow-up, confirms that rerunning does not duplicate questions, and reopens the assistant while preserving the current conversation. Browser checks also open the assistant using its new dashboard button and execute the Demand variability quick question, alongside the existing chart, table, filter and CSV checks.

## Assistant import compatibility fix

Assistant callbacks now live in `modules/assistant_actions.py`. The app no longer imports `open_assistant` or `queue_question` from the existing filter-helper module. A regression test supplies a simulated older `modules.usability` module without those functions, then checks application startup and the dashboard's assistant summary action. The full suite reports **33 passed**. This verifies the code path locally; the live Streamlit Cloud instance must load the new revision before its deployed state can be confirmed.

## Visual polish and navigation cleanup

The full automated suite reports **33 passed** after the layout, theme and navigation changes. Regression checks use the updated page/tab names while retaining the original KPI names and source totals. Browser checks cover desktop/mobile layouts, chart hover explanations, tabs, SKU selection, assistant launch/quick questions and downloads. No KPI calculation, classification cutoff or forecast algorithm changed.

## Dashboard layout redesign

The version before restructuring is saved as `dashboard-before-layout-redesign-2026-10-21`. The complete automated suite passed **33 tests**; after the division-measure switch was added, the four Streamlit UI tests also passed. The overview layout test now checks a single canvas with eight metrics, monthly/division panels and planning attention, no overview tabs or repeated Explore trend buttons, and an optional individual-KPI detail selector. Browser checks exercise the Net Units and Gross Margin chart switches, optional breakdowns, all analytical pages, SupplyIQ and CSV downloads. Source totals and calculation functions are unchanged.
