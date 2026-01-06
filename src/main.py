import os
from pathlib import Path
from typing import Iterable, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

from competitors_data import refresh_competitors_json
from index_summary import refresh_index_summary
from sales_dashboard import refresh_sales_dashboard

load_dotenv()

DATA_FILE = Path(os.getenv("DATA_FILE") or "data/autotrust_ads.csv")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR") or "outputs")
CHARTS_DIR = Path(os.getenv("CHARTS_DIR") or OUTPUT_DIR / "charts")
REPORTS_DIR = Path(os.getenv("REPORTS_DIR") or OUTPUT_DIR / "reports")
SALES_DATA_FILE = Path(os.getenv("SALES_DATA_FILE") or "data/sale2025122315296397.xlsx")
COMPETITOR_FILE = Path(os.getenv("COMPETITOR_FILE") or "data/competitor.xlsx")
COMPETITORS_JSON = Path(os.getenv("COMPETITORS_JSON") or "data/competitors.json")
DASHBOARD_DOCS = Path(os.getenv("DASHBOARD_DOCS") or "docs/dashboard.html")
DASHBOARD_REPORT = Path(os.getenv("DASHBOARD_REPORT") or REPORTS_DIR / "dashboard.html")
INDEX_DOCS = Path(os.getenv("INDEX_DOCS") or "docs/index.html")
PLOT_FORMAT = os.getenv("PLOT_FORMAT", "png")
PLOT_DPI = int(os.getenv("PLOT_DPI", "150"))


def ensure_directories() -> None:
    """Create output directories if they are missing."""
    for path in (OUTPUT_DIR, CHARTS_DIR, REPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_dataset(path: Path) -> pd.DataFrame:
    """Load CSV data and compute derived columns required for analysis."""
    df = pd.read_csv(path)
    df["Month"] = pd.to_datetime(df["Month"])

    df["Cost_per_View"] = df.apply(
        lambda row: row["Spend"] / row["Views"]
        if pd.isna(row["Cost_per_View"])
        else row["Cost_per_View"],
        axis=1,
    )

    df["CTR_decimal"] = df["CTR"].fillna(0) / 100
    df = df.sort_values(["Campaign", "Month"]).reset_index(drop=True)

    df["Views_MoM"] = df.groupby("Campaign")["Views"].pct_change()
    df["Spend_MoM"] = df.groupby("Campaign")["Spend"].pct_change()
    df["CPV_MoM"] = df.groupby("Campaign")["Cost_per_View"].pct_change()
    df["CTR_MoM"] = df.groupby("Campaign")["CTR_decimal"].pct_change()

    df["Efficiency"] = (df["Views"] / df["Spend"]) * (1 + df["CTR_decimal"])
    return df


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate totals and weighted CTR per month."""
    all_rows = df[df["Campaign"] == "All Campaigns"].set_index("Month")
    campaign_rows = df[df["Campaign"] != "All Campaigns"]

    if not all_rows.empty:
        monthly = all_rows.rename(
            columns={"Views": "Total_Views", "Spend": "Total_Spend"}
        )[["Total_Views", "Total_Spend"]]
    else:
        monthly = campaign_rows.groupby("Month").agg(
            Total_Views=("Views", "sum"),
            Total_Spend=("Spend", "sum"),
        )

    monthly["Avg_Cost_per_View"] = monthly["Total_Spend"] / monthly["Total_Views"]

    views_per_month = campaign_rows.groupby("Month")["Views"].sum()
    weighted_ctr = ((campaign_rows["CTR_decimal"] * campaign_rows["Views"]).groupby(campaign_rows["Month"]).sum() / views_per_month) * 100
    monthly["Weighted_CTR_pct"] = weighted_ctr.reindex(monthly.index).values

    return monthly


def save_chart(fig: plt.Figure, name: str) -> Path:
    path = CHARTS_DIR / f"{name}.{PLOT_FORMAT}"
    fig.tight_layout()
    fig.savefig(path, dpi=PLOT_DPI)
    plt.close(fig)
    return path


def plot_metric_by_campaign(df: pd.DataFrame, column: str, title: str, ylabel: str, filename: str) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    for campaign, group in df.groupby("Campaign"):
        ax.plot(group["Month"], group[column], marker="o", label=campaign)

    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel(ylabel)
    ax.legend()
    return save_chart(fig, filename)


def plot_campaign_bar(df: pd.DataFrame, column: str, title: str, ylabel: str, filename: str) -> Path:
    pivoted = df.pivot(index="Month", columns="Campaign", values=column)
    fig, ax = plt.subplots(figsize=(9, 5))
    pivoted.plot(kind="bar", ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel(ylabel)
    ax.legend(title="Campaign")
    return save_chart(fig, filename)


def plot_all_charts(df: pd.DataFrame) -> Tuple[Path, ...]:
    charts = []
    charts.append(
        plot_metric_by_campaign(
            df,
            "Views",
            "Landing Page Views Over Time",
            "Views",
            "views_over_time",
        )
    )
    charts.append(
        plot_metric_by_campaign(
            df,
            "Spend",
            "Spend Over Time (€)",
            "Spend (€)",
            "spend_over_time",
        )
    )
    charts.append(
        plot_metric_by_campaign(
            df,
            "Cost_per_View",
            "Cost per View Over Time",
            "Cost per View (€)",
            "cost_per_view_over_time",
        )
    )
    charts.append(
        plot_metric_by_campaign(
            df,
            "CTR_decimal",
            "CTR Trend",
            "CTR (decimal)",
            "ctr_trend",
        )
    )
    charts.append(
        plot_campaign_bar(
            df,
            "Views",
            "Views by Campaign and Month",
            "Views",
            "views_by_campaign_month",
        )
    )
    return tuple(charts)


def save_interactive_chart(fig: "px.Figure", name: str) -> Path:
    path = CHARTS_DIR / f"{name}.html"
    fig.write_html(path, include_plotlyjs="cdn", full_html=True)
    return path


def plot_interactive_charts(df: pd.DataFrame) -> Tuple[Path, ...]:
    charts: list[Path] = []

    charts.append(
        save_interactive_chart(
            px.line(
                df,
                x="Month",
                y="Views",
                color="Campaign",
                markers=True,
                title="Landing Page Views Over Time (Interactive)",
                labels={"Month": "Month", "Views": "Views"},
            ),
            "interactive_views_over_time",
        )
    )

    charts.append(
        save_interactive_chart(
            px.line(
                df,
                x="Month",
                y="Spend",
                color="Campaign",
                markers=True,
                title="Spend Over Time (€) — Interactive",
                labels={"Month": "Month", "Spend": "Spend (€)"},
            ),
            "interactive_spend_over_time",
        )
    )

    charts.append(
        save_interactive_chart(
            px.line(
                df,
                x="Month",
                y="Cost_per_View",
                color="Campaign",
                markers=True,
                title="Cost per View Over Time — Interactive",
                labels={"Month": "Month", "Cost_per_View": "Cost per View (€)"},
            ),
            "interactive_cost_per_view_over_time",
        )
    )

    ctr_df = df.copy()
    ctr_df["CTR_pct"] = ctr_df["CTR_decimal"] * 100
    charts.append(
        save_interactive_chart(
            px.line(
                ctr_df,
                x="Month",
                y="CTR_pct",
                color="Campaign",
                markers=True,
                title="CTR Trend — Interactive",
                labels={"Month": "Month", "CTR_pct": "CTR (%)"},
            ),
            "interactive_ctr_trend",
        )
    )

    charts.append(
        save_interactive_chart(
            px.bar(
                df,
                x="Month",
                y="Views",
                color="Campaign",
                barmode="group",
                title="Views by Campaign and Month — Interactive",
                labels={"Month": "Month", "Views": "Views"},
            ),
            "interactive_views_by_campaign_month",
        )
    )

    return tuple(charts)


def fmt_pct(value: float, *, already_percent: bool = False) -> str:
    if pd.isna(value):
        return "n/a"
    number = value if already_percent else value * 100
    return f"{number:.1f}%"


def fmt_euro(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"€{value:,.2f}"


def generate_comparative_report(
    df: pd.DataFrame,
    monthly: pd.DataFrame,
    static_charts: Iterable[Path],
    interactive_charts: Iterable[Path],
) -> Path:
    campaign_df = df[df["Campaign"] != "All Campaigns"].copy()
    months = sorted(df["Month"].unique())
    latest_month = months[-1]
    prev_month = months[-2] if len(months) > 1 else None
    latest_label = latest_month.strftime("%b %Y")

    latest_campaigns = campaign_df[campaign_df["Month"] == latest_month]
    totals = monthly.loc[latest_month]

    best_eff = latest_campaigns.sort_values("Efficiency", ascending=False).iloc[0]
    best_cpv = latest_campaigns.sort_values("Cost_per_View").iloc[0]
    worst_cpv = latest_campaigns.sort_values("Cost_per_View", ascending=False).iloc[0]
    ctr_leader = latest_campaigns.sort_values("CTR_decimal", ascending=False).iloc[0]
    ctr_laggard = latest_campaigns.sort_values("CTR_decimal", ascending=True).iloc[0]

    growth_snapshot = []
    if prev_month is not None:
        view_growth = monthly.loc[latest_month, "Total_Views"] / monthly.loc[prev_month, "Total_Views"] - 1
        spend_growth = monthly.loc[latest_month, "Total_Spend"] / monthly.loc[prev_month, "Total_Spend"] - 1
        monthly_ctr_prev = monthly.loc[prev_month, "Weighted_CTR_pct"]
        ctr_change = totals["Weighted_CTR_pct"] - monthly_ctr_prev
    else:
        view_growth = spend_growth = ctr_change = float("nan")

    if prev_month is not None:
        changes = latest_campaigns.sort_values("Views_MoM", ascending=False)
        for _, row in changes.iterrows():
            growth_snapshot.append(
                f"- {row['Campaign']}: Views {fmt_pct(row['Views_MoM'])}, Spend {fmt_pct(row['Spend_MoM'])}, CPV {fmt_pct(row['CPV_MoM'])}, CTR {fmt_pct(row['CTR_MoM'])}"
            )

    suggestions = [
        f"- Shift ~10-15% of spend from {worst_cpv['Campaign']} (CPV {fmt_euro(worst_cpv['Cost_per_View'])}) toward {best_eff['Campaign']} (CPV {fmt_euro(best_eff['Cost_per_View'])}, CTR {fmt_pct(best_eff['CTR_decimal'])}) to lean into the most efficient inventory.",
        f"- Reuse winning creatives from {ctr_leader['Campaign']} (CTR {fmt_pct(ctr_leader['CTR_decimal'])}) to uplift {ctr_laggard['Campaign']} (CTR {fmt_pct(ctr_laggard['CTR_decimal'])}); prioritize mobile-first variants and short hooks.",
        f"- Maintain pacing where views are expanding ({latest_label} MoM views {fmt_pct(view_growth)} while spend {fmt_pct(spend_growth)}). Protect CPV by pausing high-CPV segments inside {worst_cpv['Campaign']} and reinvesting into {best_cpv['Campaign']} (best CPV {fmt_euro(best_cpv['Cost_per_View'])}).",
        "- Add two weekly experiments: (1) headline/copy refresh for TOF, (2) retargeting frequency cap test to sustain CTR without inflating CPV.",
    ]

    report_lines = [
        "# AutoTrust Meta Ads — Comparative Report",
        f"Period: {months[0].strftime('%b %Y')} – {months[-1].strftime('%b %Y')}",
        "",
        "## Highlights",
        f"- Weighted CTR reached {fmt_pct(totals['Weighted_CTR_pct'], already_percent=True)} in {latest_label} (change vs prior: {fmt_pct(ctr_change, already_percent=True) if prev_month else 'n/a'}).",
        f"- Total views: {int(totals['Total_Views']):,} | Total spend: {fmt_euro(totals['Total_Spend'])} | Avg CPV: {fmt_euro(totals['Avg_Cost_per_View'])}.",
        f"- Efficiency leader: {best_eff['Campaign']} with {fmt_euro(best_eff['Cost_per_View'])} CPV and CTR {fmt_pct(best_eff['CTR_decimal'])}.",
        f"- CTR leader: {ctr_leader['Campaign']} at {fmt_pct(ctr_leader['CTR_decimal'])}; CPV leader: {best_cpv['Campaign']} at {fmt_euro(best_cpv['Cost_per_View'])}.",
        "",
        "## MoM Changes (latest month)",
    ]

    report_lines.extend(growth_snapshot if growth_snapshot else ["- Not enough history for MoM comparison."])

    report_lines.extend(
        [
            "",
            "## Recommendations",
        ]
        + suggestions
        + [
            "",
            "## Artifacts",
            "- Static charts:",
        ]
        + [f"  - {path}" for path in static_charts]
        + [
            "- Interactive charts:",
        ]
        + [f"  - {path}" for path in interactive_charts]
        + [
            "- Data source:",
            f"  - {DATA_FILE}",
        ]
    )

    report_path = REPORTS_DIR / "comparative_report.md"
    report_path.write_text("\n".join(report_lines))
    return report_path


def main() -> None:
    ensure_directories()
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_FILE}")

    df = load_dataset(DATA_FILE)
    monthly = monthly_summary(df)
    charts = plot_all_charts(df)
    interactive_charts = plot_interactive_charts(df)
    report_path = generate_comparative_report(df, monthly, charts, interactive_charts)
    updated_dashboards = refresh_sales_dashboard(
        SALES_DATA_FILE, (DASHBOARD_DOCS, DASHBOARD_REPORT)
    )
    competitors_json = refresh_competitors_json(COMPETITOR_FILE, COMPETITORS_JSON)
    updated_index = refresh_index_summary(
        SALES_DATA_FILE, COMPETITORS_JSON, (INDEX_DOCS,)
    )

    print("=== AutoTrust Meta Ads Analysis ===")
    print(f"Data rows: {len(df)}")
    print("\nMonthly totals:")
    print(monthly[["Total_Views", "Total_Spend", "Avg_Cost_per_View", "Weighted_CTR_pct"]])
    print("\nGenerated charts (static):")
    for path in charts:
        print(f"- {path}")
    print("\nGenerated charts (interactive):")
    for path in interactive_charts:
        print(f"- {path}")
    print(f"\nComparative report: {report_path}")
    if updated_dashboards:
        print("\nUpdated sales dashboards:")
        for path in updated_dashboards:
            print(f"- {path}")
    if competitors_json:
        print(f"\nUpdated competitors JSON: {competitors_json}")
    if updated_index:
        print("\nUpdated index summary:")
        for path in updated_index:
            print(f"- {path}")


if __name__ == "__main__":
    main()
