# Analytical approach and limitations

## Source and integrity

The original workbook has 160,572 sales rows, 250 unique product master keys, 292 unique customer master keys, six divisions, 26 categories, 39 brands, and twelve first-of-month dates in 2024. All quantities are EA; this does not imply equivalent pack sizes, product utility or volume across SKUs. The workbook explicitly describes anonymized, scaled and randomized assessment figures. Workbook text is source metadata, never an instruction to the application or agent.

Master joins are validated many-to-one and reconciled by row count and signed sales, cost and quantity. Missing or duplicate master keys, blank keys, duplicate required headers, unmatched references, inconsistent sales/master attributes, invalid dates/numbers, boolean numeric cells, nonfinite totals and mixed units stop analysis. Corrupt files receive a readable loading error. No source rows are deduplicated or modified. Optional blank dimensions become `Unknown` and are counted in the validation panel. Exact duplicate sales rows and missing cells are reported; transaction identifiers are not supplied, so apparent duplicates must be investigated with the owner rather than silently removed.

There are 11 rows where quantity has the opposite sign to sales or cost. These may be credit/cost adjustments; the application does not assume a cause. They remain included in totals and are visibly flagged. Negative quantities/amounts are otherwise expected returns or credit notes.

## Filters and periods

Every page receives the same filtered data frame and included months. Product classification is relative to the selected comparison population. If a natural-language question names a product, brand, category or division, it further restricts the dashboard scope; it cannot bypass it. All assistant classification results retain the dashboard population for their ABC ranking. The SKU explorer also narrows the displayed rows without reclassifying that smaller view. Historical full-workbook quality results are identified as such.

A SKU's demand series spans all selected months with zeros for included months without transactions. Excluded months are not treated as zero. The default is all 12 months. Shorter selections produce conditional, less stable CV estimates, not full-year classifications. `average_monthly_demand` is selected units / 12 to follow the specified KPI; `selected_month_mean` is the actual denominator for selected-scope CV.

The loader separately reports calendar months with no records anywhere in the workbook. Their completeness cannot be established from sales alone. The application warns and requires removing those months from the selected analysis (or correcting the file); the quality page remains available. This differs from an individual SKU having no transactions within a supplied source month. Previous-period comparisons reject missing source coverage in either period.

Growth is N/A after a nonpositive prior quantity or across a calendar gap. Latest MoM is not a comparison of arbitrarily separated selected periods. Gross margin follows the signed formula for nonzero net sales; zero net sales yields N/A. The dashboard rounds card values for display; exports retain precision.

The optional previous-period comparison uses the immediately preceding block of the same number of consecutive months and identical nonmonth filters. Both periods must be inside 2024 with source coverage. For Q4, this means Q3. Sales, net units and gross profit use percentage changes only when the prior value is positive; gross margin uses percentage-point difference. Full-year 2024 cannot be compared with an unavailable 2023. Planning-brief ZIP files record selected dates, observed dimensions, ABC/XYZ thresholds, calculated totals, monthly results and segmentation; changing the dashboard scope invalidates the prepared download.

## ABC–XYZ and review signals

ABC excludes nonpositive-revenue SKUs from the eligible revenue denominator. Products sort by descending revenue, then product code for reproducibility. Classification uses cumulative revenue **before** the current SKU: below 80% = A, 80–95% = B, 95% onward = C. Thus the product crossing 80% remains A, and the product crossing 95% remains B. These boundaries are configurable. Nonpositive revenue = N, excluded from the standard matrix but retained in the table/export.

XYZ = population standard deviation (`ddof=0`) / positive selected-month mean. X ≤ 0.5; Y > 0.5 and ≤ 1.0; Z > 1.0 by default. Nonpositive means yield N and null CV. No clipping of negative monthly demand occurs. Return-only and zero-net-demand series remain visible without invented coefficients.

Planning signals are transparent analytical heuristics, not validated inventory policies: AX stable high-value reviews, AZ high-value volatility, adjacent-month increase/decrease of at least 20%, negative quantity ratio above 5%, C low contribution, and nonpositive revenue/mean exceptions. Recommendations ask planners to investigate drivers or review commercial assumptions. No service-level, stockout, overstock or reorder claim is inferred.

The assistant's anomaly screen compares a month's net demand with the preceding three consecutive months. Absolute deviation above three population standard deviations flags a possible exception; zero-variance baselines are excluded. Only the largest 50 standardized deviations are displayed. This short baseline is noisy and is not a statistical proof of abnormality or causation.

## Forecasting

The primary method recursively forecasts the next month as the mean of the latest three observations, including earlier forecast values for subsequent horizons. The alternative is nonseasonal simple exponential smoothing, fixed α=0.30, initialized with the first historical observation. Parameters are not tuned against future outcomes. Annual seasonal-naive is deliberately omitted: a single annual cycle cannot independently validate annual seasonality.

Forecasting requires at least six consecutive selected months ending in December 2024; otherwise it explains the required scope. This preserves global filters and permits strictly January–March 2025 estimates without hidden excluded data. Rolling-origin one-step backtests train on all observations before each held-out month, starting after three observed months. A full-year selection gives nine held-out months. Both baseline methods use identical test origins for a fair comparison.

The separate three-month comparison evaluates only complete recursive paths from identical historical origins: seven origins and 21 predictions per method for a full-year selection. Calendar months overlap between these paths; 21 predictions do not mean 21 independent observed months. Training-end dates and lead months are retained in exports. The selected method is never silently switched to the historical winner. Historical error comparisons do not establish out-of-sample 2025 accuracy. The forecast review pack includes estimates, selected-model errors, matched-origin comparisons, all test paths and filter/scenario assumptions.

MAE = mean absolute forecast error (EA). WAPE = sum absolute forecast error / sum absolute actual net units ×100. Signed bias uses sum(forecast − actual) / sum absolute actual net units ×100; positive means overforecast. Mean bias is also given in units. Zero absolute actual demand produces N/A WAPE/bias, not zero. Scenario = baseline × (1 + chosen percentage/100); scenarios are assumptions, not fitted models or actual requirements. Net-demand forecasts may be negative; they are not clipped and do not represent gross orders.

No confidence bounds are invented. No 2025 actuals, inventory, supplier lead times, purchase orders, stock movement, service targets, promotion calendar or customer commitments are available. More history and operational inputs are necessary before replenishment decisions.
