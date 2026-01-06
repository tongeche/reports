import json
from pathlib import Path
from typing import Iterable

import pandas as pd

DATE_COL = "Data da Venda"
REVENUE_COL = "Valor Total de Venda"
MARGIN_COL = "Margem Líquida"
ORIGIN_COL = "Origem do Cliente"
MAKE_COL = "Marca"
MODEL_COL = "Modelo"


def load_sales_data(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df = df.dropna(subset=[DATE_COL]).copy()

    for col in (REVENUE_COL, MARGIN_COL):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def build_sales_chart_data(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["YearMonth"] = df[DATE_COL].dt.to_period("M")
    monthly = (
        df.groupby("YearMonth")
        .agg(
            revenue=(REVENUE_COL, "sum"),
            sales=(DATE_COL, "size"),
            net_margin=(MARGIN_COL, "sum"),
        )
        .sort_index()
    )

    return {
        "months": monthly.index.astype(str).tolist(),
        "revenue": monthly["revenue"].round(2).tolist(),
        "sales": monthly["sales"].astype(int).tolist(),
        "netMargin": monthly["net_margin"].round(2).tolist(),
    }


def build_sales_origin_data(df: pd.DataFrame) -> dict:
    origin_df = df.copy()
    origin_df[ORIGIN_COL] = origin_df[ORIGIN_COL].fillna("Sem origem")
    summary = (
        origin_df.groupby(ORIGIN_COL)
        .agg(sales=(DATE_COL, "size"), revenue=(REVENUE_COL, "sum"))
        .sort_values("sales", ascending=False)
    )

    return {
        "origins": summary.index.astype(str).tolist(),
        "sales": summary["sales"].astype(int).tolist(),
        "revenue": summary["revenue"].round(2).tolist(),
    }


def build_sales_year_snapshot(df: pd.DataFrame) -> dict:
    latest_year = int(df[DATE_COL].dt.year.max())
    year_df = df[df[DATE_COL].dt.year == latest_year].copy()
    year_df["YearMonth"] = year_df[DATE_COL].dt.to_period("M")

    if year_df.empty:
        return {"months": [], "sales": [], "salesDelta": [], "revenue": []}

    months = pd.period_range(
        start=year_df["YearMonth"].min(),
        end=year_df["YearMonth"].max(),
        freq="M",
    )
    monthly = (
        year_df.groupby("YearMonth")
        .agg(revenue=(REVENUE_COL, "sum"), sales=(DATE_COL, "size"))
        .reindex(months, fill_value=0)
    )

    sales = monthly["sales"].astype(int).tolist()
    sales_delta = [None] + [sales[idx] - sales[idx - 1] for idx in range(1, len(sales))]

    return {
        "months": [str(month) for month in months],
        "sales": sales,
        "salesDelta": sales_delta,
        "revenue": monthly["revenue"].round(2).tolist(),
    }


def _top_counts(series: pd.Series, top_n: int, *, unknown_label: str, other_label: str) -> tuple[list[str], list[int]]:
    counts = series.fillna(unknown_label).value_counts()
    labels = counts.index[:top_n].tolist()
    values = counts.values[:top_n].tolist()
    other_total = int(counts.values[top_n:].sum())
    if other_total:
        labels.append(other_label)
        values.append(other_total)
    return [str(label) for label in labels], [int(value) for value in values]


def build_sales_make_model_data(df: pd.DataFrame, *, make_top_n: int = 6, model_top_n: int = 8) -> dict:
    years = sorted(df[DATE_COL].dt.year.unique().tolist())
    makes_by_year: dict[str, dict[str, list]] = {}
    models_by_year: dict[str, dict[str, list]] = {}

    for year in years:
        year_df = df[df[DATE_COL].dt.year == year]
        make_labels, make_values = _top_counts(
            year_df[MAKE_COL],
            make_top_n,
            unknown_label="Desconhecida",
            other_label="Outros",
        )
        model_labels, model_values = _top_counts(
            year_df[MODEL_COL],
            model_top_n,
            unknown_label="Desconhecido",
            other_label="Outros",
        )

        makes_by_year[str(year)] = {"labels": make_labels, "values": make_values}
        models_by_year[str(year)] = {"labels": model_labels, "values": model_values}

    return {
        "years": [str(year) for year in years],
        "makesByYear": makes_by_year,
        "modelsByYear": models_by_year,
    }


def build_sales_brand_monthly_data(df: pd.DataFrame) -> dict:
    years = sorted(df[DATE_COL].dt.year.unique().tolist())
    months_by_year: dict[str, list[str]] = {}
    brands_by_year: dict[str, list[str]] = {}
    series_by_year: dict[str, dict[str, list[int]]] = {}

    for year in years:
        year_df = df[df[DATE_COL].dt.year == year].copy()
        year_df["YearMonth"] = year_df[DATE_COL].dt.to_period("M")
        year_df["MakeClean"] = year_df[MAKE_COL].fillna("Desconhecida").astype(str)

        months = pd.period_range(
            start=year_df["YearMonth"].min(),
            end=year_df["YearMonth"].max(),
            freq="M",
        )
        months_by_year[str(year)] = [str(month) for month in months]

        make_counts = year_df["MakeClean"].value_counts()
        brands = make_counts.index.tolist()
        brands_by_year[str(year)] = [str(brand) for brand in brands]

        series: dict[str, list[int]] = {}
        for brand in brands:
            brand_counts = year_df[year_df["MakeClean"] == brand]["YearMonth"].value_counts()
            series[str(brand)] = [int(brand_counts.get(month, 0)) for month in months]

        series_by_year[str(year)] = series

    return {
        "years": [str(year) for year in years],
        "monthsByYear": months_by_year,
        "brandsByYear": brands_by_year,
        "seriesByYear": series_by_year,
    }


def replace_js_object(text: str, var_name: str, data: dict) -> str:
    token = f"const {var_name} ="
    idx = text.find(token)
    if idx == -1:
        raise ValueError(f"Could not find {var_name} in dashboard")

    start = text.find("{", idx)
    if start == -1:
        raise ValueError(f"Could not find object start for {var_name}")

    depth = 0
    in_string = None
    escape = False
    end = None
    for pos in range(start, len(text)):
        char = text[pos]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == in_string:
                in_string = None
        else:
            if char in ("\"", "'"):
                in_string = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = pos
                    break

    if end is None:
        raise ValueError(f"Could not find object end for {var_name}")

    line_start = text.rfind("\n", 0, idx) + 1
    indent = text[line_start:idx]
    new_obj = json.dumps(data, ensure_ascii=False, indent=2)
    lines = new_obj.splitlines()
    new_obj = "\n".join([lines[0]] + [indent + line for line in lines[1:]])

    return text[:start] + new_obj + text[end + 1 :]


def update_dashboard_file(path: Path, data_map: dict) -> None:
    text = path.read_text()
    for name, data in data_map.items():
        text = replace_js_object(text, name, data)
    path.write_text(text)


def refresh_sales_dashboard(sales_path: Path, dashboard_paths: Iterable[Path]) -> list[Path]:
    if not sales_path.exists():
        return []

    df = load_sales_data(sales_path)
    if df.empty:
        return []

    data_map = {
        "salesChartData": build_sales_chart_data(df),
        "salesOriginData": build_sales_origin_data(df),
        "sales2025Data": build_sales_year_snapshot(df),
        "salesMakeModelData": build_sales_make_model_data(df),
        "salesBrandMonthlyData": build_sales_brand_monthly_data(df),
    }

    updated = []
    for dashboard_path in dashboard_paths:
        if dashboard_path.exists():
            update_dashboard_file(dashboard_path, data_map)
            updated.append(dashboard_path)

    return updated


if __name__ == "__main__":
    default_sales = Path("data/sale2025122315296397.xlsx")
    dashboard_paths = [Path("docs/dashboard.html"), Path("outputs/reports/dashboard.html")]
    refreshed = refresh_sales_dashboard(default_sales, dashboard_paths)
    if refreshed:
        print("Updated sales dashboards:")
        for path in refreshed:
            print(f"- {path}")
    else:
        print("No sales dashboard updates performed.")
