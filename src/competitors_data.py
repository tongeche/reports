import json
import re
from pathlib import Path
from typing import Optional

import pandas as pd


EXPECTED_COLUMNS = {
    "competitor_id": "competitor_id",
    "name": "name",
    "category": "category",
    "email": "email",
    "mobile": "mobile",
    "links": "links",
}


def load_competitors(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df.columns = [str(col).strip() for col in df.columns]
    return df


def normalize_links(value: Optional[str]) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[;|,]", value)
    return [part.strip() for part in parts if part.strip()]


def normalize_category(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return " ".join(value.split())


def build_competitors(df: pd.DataFrame) -> list[dict]:
    col_map = {str(col).strip().lower(): col for col in df.columns}

    def get_value(row: pd.Series, key: str) -> Optional[str]:
        col = col_map.get(key)
        if not col:
            return None
        raw = row[col]
        if pd.isna(raw):
            return None
        return str(raw).strip()

    competitors: list[dict] = []
    for _, row in df.iterrows():
        competitor = {
            "competitor_id": get_value(row, EXPECTED_COLUMNS["competitor_id"]),
            "name": get_value(row, EXPECTED_COLUMNS["name"]),
            "category": normalize_category(
                get_value(row, EXPECTED_COLUMNS["category"])
            ),
            "email": get_value(row, EXPECTED_COLUMNS["email"]),
            "mobile": get_value(row, EXPECTED_COLUMNS["mobile"]),
            "links": normalize_links(get_value(row, EXPECTED_COLUMNS["links"])),
        }
        competitors.append(competitor)
    return competitors


def refresh_competitors_json(source_path: Path, output_path: Path) -> Optional[Path]:
    if not source_path.exists():
        return None

    df = load_competitors(source_path)
    if df.empty:
        return None

    competitors = build_competitors(df)
    output_path.write_text(
        json.dumps(competitors, ensure_ascii=False, indent=2)
    )
    return output_path


if __name__ == "__main__":
    source = Path("data/competitor.xlsx")
    output = Path("data/competitors.json")
    updated = refresh_competitors_json(source, output)
    if updated:
        print(f"Updated competitors JSON: {updated}")
    else:
        print("No competitors JSON updates performed.")
