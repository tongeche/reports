# AutoTrust Meta Ads Analysis

Small Python project that loads a CSV dataset and generates charts plus a short report.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

## Inputs and outputs

- Input CSV: `data/autotrust_ads.csv`
- Ads PDF reports: `Relatório*Meta Ads*Autotrust*.pdf`
- Competitors XLS: `data/competitor.xlsx`
- Competitors JSON: `data/competitors.json`
- Ads reports JSON: `data/ads_reports.json`
- Index page: `docs/index.html`
- Outputs: `outputs/charts/` and `outputs/reports/`

## Optional config (env vars)

- `DATA_FILE` (default: `data/autotrust_ads.csv`)
- `SALES_DATA_FILE` (default: `data/sale2025122315296397.xlsx`)
- `COMPETITOR_FILE` (default: `data/competitor.xlsx`)
- `COMPETITORS_JSON` (default: `data/competitors.json`)
- `INDEX_DOCS` (default: `docs/index.html`)
- `OUTPUT_DIR` (default: `outputs`)
- `PLOT_FORMAT` (default: `png`)
- `PLOT_DPI` (default: `150`)

Using Matplotlib + ReportLab.

### **Predictive modelling**

Forecast:

* Views
* Spend
* Cost per result

---
