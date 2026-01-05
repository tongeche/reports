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
- Outputs: `outputs/charts/` and `outputs/reports/`

## Optional config (env vars)

- `DATA_FILE` (default: `data/autotrust_ads.csv`)
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
