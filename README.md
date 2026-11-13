# SupplyIQ — Consumer Supply Planning Intelligence

A Streamlit dashboard for the supplied **Assignment_Supply_Planner_Consumer.xlsx**, with executive reporting, SKU prioritization, demand estimates and a conversational assistant. Calculations use the real workbook, including its signed returns and credit notes. No demonstration data, stock balances or supplier information are added.

The interface uses navy, muted gold and warm white, with a focused overview, interactive charts and help beside each measure. Original technical names such as **MoM Demand Growth**, **ABC–XYZ**, **Demand CV**, **MAE** and **WAPE** remain intact; their explanations use simple language.

## Run locally

Use Python **3.12**, the tested version. Python 3.11 is also supported; Python 3.14 has not been validated for this project.

Run these commands in the repository folder:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate` instead. Open the local URL printed by Streamlit, normally `http://localhost:8501`.

The original workbook is included in `data/`. It contains 160,572 sales rows, 250 product master keys, 292 customer master keys and twelve months of 2024 history. The sidebar also accepts a replacement `.xlsx` with the same four sheets, required columns and 2024 scope. Loading validates the workbook before analysis; subsequent interactions use a bounded, content-keyed Streamlit data cache. No external database or API key is needed.

## Find your way around

Global Month, Division, Category, Brand, Product, Customer Type, Country and Sales Channel filters apply to the analytics and assistant. Division → Category → Brand → SKU choices cascade. Quick period controls include **Full year**, **Last 6 months** and **Q4 only**. Empty dimension selections mean all available values; an empty month selection contains no data.

If a replacement workbook omits an entire calendar month, the app warns and asks you to choose months present in the source. It does not assume the missing file history represents zero demand. The original workbook has all twelve months.

| Workspace | What you can do |
| --- | --- |
| **Executive overview** | Review four headline KPIs, supporting KPIs, sales and demand trends, division performance, leading products, category/channel contributions and calculated planning observations. |
| **SKU analysis** | Configure ABC/XYZ thresholds, explore Pareto and the nine-cell matrix, combine class/focus filters, sort the SKU explorer and select a product for its history. |
| **Demand forecasting** | Compare two explainable baseline models, inspect historical forecast errors and simulate January–March 2025 demand changes for a portfolio, category or SKU. |
| **SupplyIQ assistant** | Ask real-data questions, continue with follow-ups, inspect tables/charts and download results or the current conversation. |
| **Data quality & downloads** | Inspect workbook checks, reconciliation and flagged records, then download selected records and reports. |

Hover over a chart's **About this chart** help indicator for its purpose, units and limitations; tap it on touch screens. Chart points show actual values. Clickable SKU rows open demand history. Empty selections show a useful message instead of an empty chart.

## Review and export tools

- **Executive overview → Review tools:** optionally compare the selected consecutive months with the immediately preceding, equal-length period using the same product/customer filters. Both periods must fit within 2024. For example, Q4 compares with July–September; full-year 2024 has no prior year in this workbook. Sales, units and profit use percentage change where valid; margin uses percentage-point change.
- **Prepare planning brief:** creates a local ZIP containing a readable summary, KPI totals, monthly trends, SKU segmentation and scope/threshold metadata for the current selection. Downloading does not publish it anywhere.
- **SKU explorer:** combine ABC and XYZ classes, search, planning focus and sorting. Applying a matrix segment narrows the explorer; classifications remain relative to the dashboard population. Export either the visible explorer rows or the complete dashboard-scoped segmentation.
- **Forecast review pack:** download estimates, the selected model's backtest, one- and three-month model comparisons, all forecast test paths and recorded assumptions together in a ZIP. Individual CSV downloads remain available.
- **Data quality:** inspect and download selected records with sign differences, exact repeated records or financial values with zero quantity. These are review candidates, not automatically confirmed errors; no source rows are silently removed.

## SupplyIQ assistant

Use **Ask SupplyIQ** or the floating assistant button to open chat while keeping the current dashboard page. **Summarize my selection** starts a calculated summary. The dedicated assistant page shares the same conversation. Starter buttons, **Top 10 SKUs**, **Monthly demand**, **More questions** and a text box make common analyses easy to reach.

Useful questions include:

- “Which 10 SKUs generated the highest sales in 2024?”
- “Top 5 SKUs by units for Brand 10.”
- “Which products have the biggest demand swings?”
- “Compare Food and Personal Care demand.”
- “Compare P001 and P002 demand history.”
- “Which products belong to the AZ category?”
- “What was the monthly demand growth for Brand 10?”
- “Explain the ABC–XYZ classification of P001.”

Follow-ups such as “What about Brand 10?” reuse the preceding analysis. A new named entity replaces the previous question focus, while dashboard filters always apply. The assistant displays its narrower question focus and preserves dashboard-wide ABC classifications when a question names a brand, category or product. Comparison series include selected months with no sales as zero. Unsupported questions or unavailable years receive an explanation rather than invented figures; stock and supplier questions identify the missing information.

**New chat** clears the conversation. **Settings → Download conversation** saves retained messages and calculated results as a local Markdown file. History is session-local, shared between the page and dialog, limited to 20 messages and reset when the workbook, filters or classification thresholds change. Transcript exports omit internal configuration and redact common API-key/password/token patterns; avoid entering credentials into chat.

### Optional LLM configuration

The built-in assistant works without a paid API. To enable optional OpenAI interpretation, export `OPENAI_API_KEY` and optionally `OPENAI_MODEL` (default `gpt-4o-mini`), or create an untracked `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your-key-entered-securely"
OPENAI_MODEL = "gpt-4o-mini"
```

Then enable **Settings → Use optional AI service** in SupplyIQ. `.env.example` documents the variables; `.env` files are not automatically loaded. Never commit real credentials. This mode requires access to `api.openai.com`.

Local recognition determines supported analytical intents; an optional model can interpret otherwise unsupported wording and explain verified aggregate results. Analytical execution uses code-owned, parameterized DuckDB `SELECT` templates or controlled Pandas functions. Model-generated SQL, shell commands and arbitrary code are never executed. The optional service receives the question, short context and up to 15 aggregate result rows, not the raw transaction table. AI explanations are separately labelled; calculated results remain authoritative. API failures fall back to built-in analysis without exposing provider errors or credentials. A live API-key integration is not claimed as validated here.

## Definitions and planning limits

See [methodology](docs/METHODOLOGY.md) for detailed assumptions and [verified executive findings](docs/EXECUTIVE_SUMMARY.md) for assessment talking points.

| Measure | Definition |
| --- | --- |
| Net Sales | Sum of signed revenue. |
| Net Units Sold / net demand | Sum of signed quantities: units sold minus returns. |
| Gross Profit | Net Sales − signed Cost of Sales. |
| Gross Margin % | Gross Profit / nonzero Net Sales × 100. Negative-revenue margins require care. |
| MoM Demand Growth % | (Current − previous quantity) / previous quantity × 100, only for adjacent selected months with positive previous quantity. |
| Average Monthly Net Demand | Selected net quantity / 12. For a partial-year selection, this is its contribution to the annual average, not its selected-month mean. |
| Negative Transaction Quantity Rate % | Absolute negative units / positive units × 100. It measures units, not the percentage of transaction rows. |
| ABC | Rank positive net SKU revenue against eligible positive SKU revenue; defaults A = first 80%, B = next 15%, C = rest. Nonpositive revenue is N. A threshold-crossing SKU stays in the class where its contribution begins. |
| XYZ | Population standard deviation / positive mean over included months; defaults X ≤ 0.5, Y ≤ 1.0, Z > 1.0. Genuine no-sales months are zero; excluded months are omitted. Nonpositive means have no CV and use N. |

Undefined ratios display **N/A**, not zero. The workbook uses EA throughout, but adding units across SKUs does not imply equivalent pack sizes or volume. Revenue and units remain signed; unusually negative transactions are reasons to investigate, not proof of a cause.

Forecasting requires at least six consecutive selected months ending in December 2024. It compares a recursive three-month moving average with fixed-alpha exponential smoothing. Both models are evaluated using the same historical origins for each one- or three-month design, with MAE, WAPE and bias where defined. Three-month paths overlap, so their forecast counts are not independent calendar months. Only 12 months of history are available: backtest results do not establish future accuracy or learned annual seasonality. January–March 2025 outputs and growth/decline scenarios are **illustrative demand estimates**, never actual sales or purchase requirements.

Inventory on hand, stock movements, lead times and purchase orders are absent. The app therefore cannot establish stock coverage, overstock, stockout risk, service levels or replenishment quantities. Planning signals identify products for investigation.

## Deploy on Streamlit Community Cloud

1. Use this project's GitHub repository, **`faaayaaz/analytics`**, with the desired version on `main`.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), create an app, select the repository and `main`, and set the entrypoint to **`app.py`** at the repository root. Choose Python **3.12**.
3. Dependencies install from `requirements.txt`. Theme/server settings are in `.streamlit/config.toml`; the included workbook must remain in `data/`. No database provisioning is needed.
4. Optionally add `OPENAI_API_KEY` and `OPENAI_MODEL` in the app's secure Secrets settings. Without them, the local assistant stays operational.
5. Open the deployed URL and check all five pages, a filter change, an assistant question and a download. For an existing deployment tracking `main`, check its build status after a push and reboot from **Manage app** if needed.

Pushing source to GitHub and publishing a Streamlit app are separate steps. This documentation does not claim a live Cloud deployment. The app has no authentication or enterprise access-control layer; choose deployment visibility appropriate to the workbook's sensitivity.

## Validation and project structure

Run the automated analytical and Streamlit tests from the repository folder:

```bash
python -m pytest -q
```

Validation covers workbook loading/joins, metric reconciliation, classifications and edge cases, filtered assistant results, forecast backtests, review exports and page interactions. See [validation notes](docs/VALIDATION.md) for recorded evidence and limits. Optional browser checks require Playwright and Chromium; they are not runtime dependencies.

The current local suite passes **85 tests**. GitHub Actions is configured to run the analytical and Streamlit suite on pushes to `main` and pull requests. For live browser checks with the app running, use `python tests/browser_smoke.py`, `python tests/assistant_browser_smoke.py` and `python tests/advancement_browser_smoke.py`.

[Current desktop overview](docs/screenshots/supplyiq-advancements-desktop.png) · [Filtered SKU explorer](docs/screenshots/supplyiq-advancements-explorer.png)

```text
app.py                         # Navigation, global scope, cached workbook loading
modules/data_loader.py         # Workbook schema, master joins and validation
modules/kpi_calculations.py     # Metrics, summaries and calculated insights
modules/abc_xyz_analysis.py     # Classification and planning signals
modules/period_comparison.py   # Equal-length comparisons within 2024
modules/reporting.py           # Local planning brief and flagged-record exports
modules/forecasting.py         # Models, scenarios, backtests and review pack
modules/ai_assistant.py         # Local intents, fixed query tools, optional LLM
modules/assistant_ui.py         # Shared page/dialog chat and transcript download
modules/views.py                # Analytics workspaces and export controls
modules/palette.py              # Shared navy/gold chart colours
tests/                         # Analytical and interface regression checks
data/                          # Original assessment workbook
docs/                          # Methodology, verified findings and validation
```

Runtime dependencies are in `requirements.txt`; tested direct package versions are in `requirements.lock.txt`. Use `pip install -r requirements.lock.txt` to reproduce those versions. Streamlit 1.66 or newer is required for the current chat/dialog controls.

## Saved versions

The version immediately before these advancements is preserved by the tag **`supplyiq-before-advancements-2026-11-13`**. The original dashboard is preserved as **`dashboard-v1-original`**; earlier redesign tags remain in Git history.

To inspect the saved version on a separate local branch:

```bash
git fetch origin --tags
git switch -c review-before-advancements supplyiq-before-advancements-2026-11-13
```

Restore a previous version to `main` through a new commit so newer work remains recoverable. Historical screenshots and design notes in `docs/` may depict older versions; this README describes the current navy/gold interface.
