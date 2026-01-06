import json
from pathlib import Path
from typing import Iterable

import pandas as pd

from sales_dashboard import DATE_COL, ORIGIN_COL, load_sales_data, replace_js_object


def _top_counts(
    series: pd.Series,
    top_n: int,
    *,
    unknown_label: str,
    other_label: str,
) -> tuple[list[str], list[int]]:
    cleaned = (
        series.fillna(unknown_label)
        .astype(str)
        .str.strip()
        .replace("", unknown_label)
    )
    counts = cleaned.value_counts()
    labels = counts.index[:top_n].tolist()
    values = counts.values[:top_n].tolist()
    other_total = int(counts.values[top_n:].sum())
    if other_total:
        labels.append(other_label)
        values.append(other_total)
    return [str(label) for label in labels], [int(value) for value in values]


def build_sales_yearly_data(df: pd.DataFrame) -> dict:
    if df.empty or DATE_COL not in df.columns:
        return {"years": [], "sales": []}

    summary = df.groupby(df[DATE_COL].dt.year).size().sort_index()
    return {
        "years": summary.index.astype(int).astype(str).tolist(),
        "sales": summary.astype(int).tolist(),
    }


def build_origin_distribution_data(df: pd.DataFrame, *, top_n: int = 5) -> dict:
    if df.empty or ORIGIN_COL not in df.columns:
        return {"origins": [], "counts": []}

    labels, values = _top_counts(
        df[ORIGIN_COL],
        top_n,
        unknown_label="Sem origem",
        other_label="Outros",
    )
    return {"origins": labels, "counts": values}


def build_competitor_category_data(path: Path, *, top_n: int = 4) -> dict:
    if not path.exists():
        return {"categories": [], "counts": []}

    try:
        competitors = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {"categories": [], "counts": []}

    if not competitors:
        return {"categories": [], "counts": []}

    categories = pd.Series([item.get("category") for item in competitors])
    labels, values = _top_counts(
        categories,
        top_n,
        unknown_label="Sem categoria",
        other_label="Outros",
    )
    return {"categories": labels, "counts": values}


def update_index_file(path: Path, data_map: dict) -> None:
    text = path.read_text()
    for name, data in data_map.items():
        text = replace_js_object(text, name, data)
    path.write_text(text)


def refresh_index_summary(
    sales_path: Path,
    competitors_path: Path,
    index_paths: Iterable[Path],
) -> list[Path]:
    data_map: dict[str, dict] = {}

    if sales_path.exists():
        df = load_sales_data(sales_path)
        data_map["indexSalesYearlyData"] = build_sales_yearly_data(df)
        data_map["indexOriginDistributionData"] = build_origin_distribution_data(df)

    if competitors_path.exists():
        data_map["indexCompetitorCategoryData"] = build_competitor_category_data(
            competitors_path
        )

    if not data_map:
        return []

    updated = []
    for path in index_paths:
        if path.exists():
            update_index_file(path, data_map)
            updated.append(path)

    return updated


if __name__ == "__main__":
    default_sales = Path("data/sale2025122315296397.xlsx")
    competitors_json = Path("data/competitors.json")
    index_paths = [Path("docs/index.html")]
    refreshed = refresh_index_summary(default_sales, competitors_json, index_paths)
    if refreshed:
        print("Updated index summary:")
        for path in refreshed:
            print(f"- {path}")
    else:
        print("No index summary updates performed.")
