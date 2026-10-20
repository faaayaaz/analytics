# Consumer Supply Planning Intelligence

A working Streamlit assessment dashboard for the uploaded **Assignment_Supply_Planner_Consumer.xlsx**. Five workspaces provide executive metrics, SKU planning intelligence, a forecasting simulator, a conversational analytical assistant, and data quality/exports. All production calculations use the actual workbook; there is no generated demonstration dataset.

## Run locally

Requires Python 3.11 or 3.12. Tested on Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The supplied workbook is in `data/`. The sidebar can replace it with another workbook using the same four sheets, column schema and 2024 scope. First load parses and validates Excel; subsequent interactions use Streamlit's bounded, content-keyed data cache. The 160,572-row file is supported without API access or external database services.

```bash
python -m pytest -q
```

## Workspaces

- **Executive overview:** eight KPI cards with interactive definitions, sales/demand trends, division revenue and margin, top products, categories, channels, growth heatmap and calculated insights.
- **SKU & demand intelligence:** configurable ABC/XYZ boundaries, Pareto, nine-cell matrix, segment exploration, explicit attention criteria, searchable SKU workbench, product histories and segmentation CSV.
- **Forecasting & scenario lab:** selected portfolio, category or SKU; recursive three-month average and fixed-alpha exponential smoothing; rolling backtests; January–March 2025 estimates; growth/decline scenario and CSV export.
- **SupplyIQ assistant:** real-data natural-language analysis, follow-up context, result tables, charts and downloads. Works without an API key. Optional LLM interpretation uses allowlisted tools and verified aggregate evidence.
- **Data quality & exports:** master relationship validation, missing/duplicate checks, financial reconciliation, sign issues, source notes, and filtered transaction/report downloads.

Month, Division, Category, Brand, Product, Customer Type, Country and Sales Channel filters apply consistently to all analytical pages and assistant tools. Cascading dimensions support Division → Category → Brand → SKU exploration. No selected dimension values means “all available”; no selected months means no records. The quality panel explicitly reports full-workbook validation separately from filtered figures.

## SupplyIQ configuration and security

No key is required. Local intent recognition computes top SKUs, demand CV, division comparisons, all nine segments, declining categories, brand trends, SKU details, attention signals, historical anomalies and executive insights. Multi-turn follow-ups such as “What about Brand 10?” reuse the preceding analytical intent. Unsupported questions receive a capability explanation rather than invented answers. Inventory and supplier questions receive a missing-data response.

To enable optional OpenAI interpretation, export `OPENAI_API_KEY` and optionally `OPENAI_MODEL` (default `gpt-4o-mini`), or use an untracked `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your-key-entered-securely"
OPENAI_MODEL = "gpt-4o-mini"
```

Then enable the explicit LLM toggle on the assistant page. `.env.example` documents shell variables; `.env` files are **not automatically loaded**. Never commit real credentials. Network access to `api.openai.com` is required for this optional mode.

The model first chooses an enumerated intent. Local code executes fixed, parameterized DuckDB SELECT templates or controlled Pandas functions; model-generated SQL/code is never executed. A second optional call explains the verified aggregates. It receives the question, context and up to 15 aggregate result rows, not the transaction table. Calculated tables and deterministic narrative remain authoritative; AI interpretation is separately labeled and may need review. API errors fall back to local calculations without exposing credentials or provider error bodies. History is session-local, bounded and cleared on changes to workbook, filter scope or thresholds. No database, writes, external browsing, shell tools or arbitrary model functions are exposed to the assistant.

## Analytical definitions and scope

See [methodology](docs/METHODOLOGY.md) for edge cases and forecast assumptions and [verified executive findings](docs/EXECUTIVE_SUMMARY.md) for assessment talking points.

- Net sales = signed revenue; net demand = signed quantity, including credits/returns.
- Gross profit = net sales − signed cost. Gross margin = gross profit / nonzero net sales × 100. Negative revenue margins retain the formula and require careful interpretation.
- Monthly growth = (current − previous) / previous × 100, only for a positive prior-month quantity and adjacent selected calendar months.
- Average monthly net demand = selected units / 12, as requested. When months are excluded, this is selected contribution to an annual average; the selected-month mean used for CV is provided separately.
- Negative transaction quantity rate = absolute negative units / positive units × 100. This is a quantity ratio, not a transaction-count percentage.
- ABC ranks positive net SKU revenue against total eligible positive SKU revenue; nonpositive products are N. A boundary-crossing SKU stays in the class where its revenue begins, so realized shares can exceed a threshold.
- XYZ uses population standard deviation / positive mean over the included calendar months. Included months without sales are zero. Excluded months are not manufactured zero demand. Nonpositive means have no CV and use N.

## Deploy on Streamlit Community Cloud

1. Review the source and included anonymized workbook, then commit and push this project to your GitHub repository. This delivery does not push or publish automatically.
2. In Streamlit Community Cloud create an app, choose the repository/branch and set the entrypoint to `app.py` at the project root. Select Python 3.12.
3. Dependencies install from `requirements.txt`; theme/server settings are in `.streamlit/config.toml`. No database provisioning is needed.
4. Optionally add `OPENAI_API_KEY` and `OPENAI_MODEL` in the platform's secure Secrets settings. Without them the local assistant remains operational.
5. After deployment, verify all five pages, a filter change, one assistant question and a CSV download. Cloud deployment itself has not been performed or claimed here.

The workbook must remain available at the default path. Treat uploaded business files as sensitive even when the supplied assessment data is anonymized. This is an assessment analytics application, with no authentication or enterprise access-control layer; choose deployment visibility accordingly.

## Project structure

```text
app.py                         # UI shell, global scope, cached workbook loading
modules/data_loader.py         # Schema, master joins, validation, filtering
modules/kpi_calculations.py     # Shared metrics, summaries, dynamic insights
modules/abc_xyz_analysis.py     # Classification and review signals
modules/forecasting.py          # Baselines, scenarios, rolling backtests
modules/ai_assistant.py         # Local intents, fixed DuckDB tools, optional LLM
modules/visualizations.py       # Consistent interactive chart rendering
modules/views.py                # Five page renderers and downloads
tests/                        # See tests/ for analytical and Streamlit tests
data/                          # Original assessment workbook
docs/                          # Methodology, executive summary, validation
```

Runtime dependencies are declared in `requirements.txt`; tested versions are recorded in `requirements.lock.txt`. Use `pip install -r requirements.lock.txt` to reproduce the tested direct versions. Optional browser validation uses Playwright and a local Chromium installation; neither is required to run the dashboard.

## Usability update and preserved original

The original tested dashboard is preserved on GitHub as the annotated tag **`dashboard-v1-original`**, pointing to commit `c7d5a45`. This tag was pushed before any usability edits. Browse or download that version from the repository's Tags list. To inspect it locally without discarding the updated version:

```bash
git fetch origin --tags
git switch -c review-original dashboard-v1-original
```

To restore the deployed app later, ask to restore the original tag to `main` through a new commit; avoid force-pushing or deleting newer history.

The updated interface adds:

- One-click **Full year**, **Q4 only**, and **Reset all filters** controls.
- Automatic removal of incompatible downstream filter choices when drilling into a different division/category.
- A visible active-filter summary, searchable filter hints, and recovery from an empty month selection.
- A **New here?** guide with shortcuts to SKU review, forecast scenarios and the assistant.
- Clickable SKU workbench rows that open the selected product's demand history; manual product selection remains available.
- **−20% / baseline / +20%** forecast scenario buttons and three-month baseline, scenario and estimated-change summaries.

These controls reuse the original analytical functions and preserve the underlying metric definitions and data.
