

## 📌 Project: AutoTrust Meta Ads — Trend Analysis (Sept–Nov 2025)

This file contains the structured dataset, schema, and analysis plan for building a small Python program that processes and visualizes trends extracted from the Meta Ads monthly reports (September, October, November 2025).

---

# 1. Dataset Overview

Data was extracted from PDF reports for:

* **September 2025**
* **October 2025**
* **November 2025**

The reports contain metrics grouped by campaign type:

* **All Campaigns (Monthly Summary)**
* **Topo de Funil — Maia**
* **Topo de Funil — Portugal**
* **Remarketing**

Each category includes:

* *Landing Page Views (LPV)*
* *Spend (€)*
* *Cost per Landing Page View (CPLPV)*
* *Click-Through Rate (CTR %)*

Not all metrics exist for the All-Campaigns summary.

---

# 2. Data Structure (CSV / DataFrame Model)

Your Python program will load a dataset structured like this:

```csv
Month,Campaign,Views,Spend,Cost_per_View,CTR
2025-09,All Campaigns,10885,478.17,,
2025-09,Maia TOF,2514,149.53,0.06,2.63
2025-09,Portugal TOF,5058,193.46,0.04,4.03
2025-09,Remarketing,3313,135.18,0.04,3.95

2025-10,All Campaigns,12976,495.02,,
2025-10,Maia TOF,2566,154.76,0.06,2.70
2025-10,Portugal TOF,7042,201.02,0.03,4.67
2025-10,Remarketing,3368,139.24,0.04,3.82

2025-11,All Campaigns,13531,480.66,,
2025-11,Maia TOF,2899,149.76,0.05,2.98
2025-11,Portugal TOF,7245,195.46,0.03,4.29
2025-11,Remarketing,5587,135.44,0.02,4.19
```

---

# 3. Schema Definition

| Column            | Type                   | Description                                                                |
| ----------------- | ---------------------- | -------------------------------------------------------------------------- |
| **Month**         | `datetime` or `string` | Year-month of report (YYYY-MM)                                             |
| **Campaign**      | `string`               | One of: `"All Campaigns"`, `"Maia TOF"`, `"Portugal TOF"`, `"Remarketing"` |
| **Views**         | `int`                  | Landing page views                                                         |
| **Spend**         | `float`                | Amount spent in euros                                                      |
| **Cost_per_View** | `float` or `None`      | Spend ÷ Views (if provided or to be computed)                              |
| **CTR**           | `float` or `None`      | Click-through rate (percentage)                                            |

---

# 4. Analysis Goals (for the Python Program)

Your program should compute:

### **4.1. Monthly Aggregates**

* Total views per month
* Total spend per month
* Average cost per view
* Weighted CTR (based on views)

### **4.2. Trend Metrics (MoM)**

For each campaign type:

* Month-over-month growth in views
* Month-over-month change in spend
* Change in cost-per-view
* CTR evolution

For example:

```
views_growth = (views_current - views_previous) / views_previous
```

### **4.3. Campaign Efficiency Scoring**

Assign a performance score per campaign:

```
score = (views / spend) * CTR_weight
```

Where:

* High views + low spend = more efficient
* Higher CTR should boost the score

Example weights:

```python
CTR_weight = 1 + (CTR / 100)
```

### **4.4. Visualizations**

The program should generate:

1. **Views Over Time** (line chart)
2. **Spend Over Time**
3. **Cost per View Comparison**
4. **CTR Trend**
5. **Bar chart comparing campaigns per month**

---

# 5. Python Program Outline

Use this as a blueprint for your `main.py`:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load CSV
df = pd.read_csv("autotrust_ads.csv")

# Convert Month to datetime
df["Month"] = pd.to_datetime(df["Month"])

# Compute cost per view where missing
df["Cost_per_View"] = df.apply(
    lambda row: row["Spend"] / row["Views"] if pd.isna(row["Cost_per_View"]) else row["Cost_per_View"],
    axis=1
)

# Compute MoM trends
df["Views_MoM"] = df.groupby("Campaign")["Views"].pct_change()
df["Spend_MoM"] = df.groupby("Campaign")["Spend"].pct_change()
df["CPV_MoM"] = df.groupby("Campaign")["Cost_per_View"].pct_change()

# CTR normalize (convert percent → decimal)
df["CTR_decimal"] = df["CTR"] / 100

# Efficiency Score
df["Efficiency"] = (df["Views"] / df["Spend"]) * (1 + df["CTR_decimal"])
```

### Visualization Example:

```python
plt.plot(df[df["Campaign"]=="All Campaigns"]["Month"],
         df[df["Campaign"]=="All Campaigns"]["Views"])
plt.title("Landing Page Views — All Campaigns")
plt.xlabel("Month")
plt.ylabel("Views")
plt.show()
```

---

# 6. Suggested File Structure (VS Code)

```
autotrust-analysis/
│
├── data/
│   └── autotrust_ads.csv
│
├── src/
│   └── main.py
│
├── analysis_notes.md  ← (this file)
│
└── outputs/
    ├── charts/
    └── reports/
```

---

# 7. Future Extensions

### **Add more months automatically**

You can later create a script to append new PDF-extracted data.

### **Auto-generate monthly PDF reports**

Using Matplotlib + ReportLab.

### **Predictive modelling**

Forecast:

* Views
* Spend
* Cost per result

---

