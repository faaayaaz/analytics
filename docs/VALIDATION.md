# Validation record

Validated in the supplied Linux cloud environment on Python 3.12 using the actual assessment workbook. Direct package versions are recorded in `requirements.lock.txt`.

## Current release — November 13, 2026

The final automated suite passed **85 tests** in 85.70 seconds. Ruff's F checks, Python compilation and `git diff --check` also passed. The earlier sections below are historical validation records.

New coverage verifies:

- Like-for-like Q4/Q3 comparisons under the same dimension filters, invalid prior periods, missing source coverage, and margin percentage-point differences.
- Planning-brief ZIP reconciliation across KPI, monthly and segmentation files; threshold/scope metadata; prepared-download invalidation after filter changes.
- Combined SKU class/focus/search/sort controls, the 14-product AZ segment, literal search, empty states, reset and filtered product history.
- Both forecast models on matched one-month origins and complete three-month paths, no future leakage, signed/zero-demand handling and the review-pack contents.
- Assistant ABC population consistency, replacement/retention of entity focus, units-to-sales ranking follow-ups, brand/category comparison dimensions, filtered-out named entities, unsupported years and transcript redaction.
- Corrupt uploads, blank identifiers, duplicate headers, boolean/nonfinite numeric values, scoped KPIs, calendar gaps and incomplete-workbook recovery.

Fresh Chromium runs of `tests/browser_smoke.py` and `tests/advancement_browser_smoke.py` passed against the finished local app. They covered all five pages, Plotly hover/zoom/autoscale, filter changes, SKU selection, assistant execution, exports and a 390-pixel mobile layout without main-content overflow. The new browser checks downloaded and inspected the Q4 planning brief (AED 113,146,628.69 net sales), 14 AZ explorer rows, four model-comparison rows, the forecast ZIP, the chat transcript and 227 flagged records. Those records comprise 11 quantity/financial sign differences and 216 financial adjustments with zero quantity; flags are review candidates, not confirmed errors. Source totals remain unchanged.

`tests/assistant_browser_smoke.py` also passed the floating launcher, typed missing-inventory response, result download, New chat, close/page preservation and mobile input checks. No paid API was used. The final source is covered by a new GitHub Actions workflow for pushes to `main` and pull requests; hosted Actions success and the live Streamlit Cloud deployment are not established by these local checks.

The pre-upgrade revision `aaaca5d` is preserved on GitHub as **`supplyiq-before-advancements-2026-11-13`**. Current previews show the navy/gold overview and the filtered SKU explorer.

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

## Premium visual redesign — November 11, 2026

The full suite passed **33 tests**, and the four Streamlit UI tests were rerun successfully during visual refinement. Chromium smoke checks passed across all five pages, including chart hover help, zoom/autoscale, Net Units/Gross Margin switches, SKU selection, SupplyIQ quick questions and CSV downloads. Fresh desktop/mobile screenshots were captured under `docs/screenshots`; a fresh 390-pixel viewport passed the no-horizontal-overflow check. The design retains source totals, original KPI definitions, shared filters and the no-key assistant. Changes are limited to presentation, styling and chart highlights; numerical planning algorithms were not modified.

Chromium and the localhost server required the approved outer execution context because this session's sandbox blocks socket creation. The deployed Streamlit Cloud instance has not been inspected; repository publication and a successful local browser run do not establish that Cloud has loaded the new revision.

## Information hierarchy redesign — November 11, 2026

The full automated suite passed **33 tests** after the structural rewrite; the four UI tests were then rerun with additional assertions that four supporting metrics sit in a collapsed section and only advanced dimension filters remain in the sidebar. Chromium confirmed exactly four visible headline KPI values, a visible top filter bar, chart switches, optional breakdowns, all five pages, SKU selection, SupplyIQ questions and reconciled CSV downloads. The redesign preserves all eight KPI definitions and underlying sales/forecast calculations. A new tag stores the previous premium layout before editing. Screenshots are saved separately from the earlier visual-design previews.

## Navy & gold theme

The complete suite passed **33 tests** after the palette, chart scale and toolbar styling changes. Chromium checks passed across the five pages, including chart help, zoom/autoscale, measure switching, SKU selection, SupplyIQ and downloads. Desktop/mobile previews were captured from the running application; the mobile overflow and four-visible-headline-KPI checks passed. Shared palette values now keep division and SKU charts consistent. The monthly-growth colour explanation was updated to match the gold-decrease/navy-increase scale. Calculations and numerical totals are unchanged.

## SupplyIQ conversation interface

The complete automated suite reports **34 passed**. Updated UI tests verify that opening a summary leaves the active dashboard page unchanged, retains the Food-filtered AED 193,130,712.74 result, preserves conversation across reopen, consumes questions once, accepts typed questions, clears on New chat and resets after filter changes. The legacy-helper import regression also passes with the dialog launcher.

The five-page Chromium smoke test passed with dialog questions and Close returning to the same forecast page. A separate `tests/assistant_browser_smoke.py` passed the floating launcher, starter questions, a reconciled 10-row CSV result led by P195, typed missing-inventory question, New chat, closing to the original overview, mobile input visibility and no horizontal overflow. Desktop/mobile screenshots were inspected and saved under `docs/screenshots`. No live API credentials were used; paid-provider limitations remain as previously documented. Analytical calculations were not changed.
