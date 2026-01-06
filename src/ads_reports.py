import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Union

from pypdf import PdfReader

MONTH_MAP = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

IGNORE_LINES = {
    "autotrust",
    "facebook & instagram ads",
    "resultados",
}


def normalize_line(line: str) -> str:
    if re.search(r"(?:\b\w\b\s+){3,}\b\w\b", line):
        line = re.sub(r"(?<=\w)\s(?=\w)", "", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line


def parse_number(raw: str) -> Optional[Union[float, int]]:
    cleaned = (
        raw.replace("€", "")
        .replace("%", "")
        .replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if value.is_integer():
        return int(value)
    return round(value, 4)


def parse_number_from_text(text: str) -> Optional[Union[float, int]]:
    match = re.search(r"(\d[\d\s.,]*)", text)
    if not match:
        return None
    return parse_number(match.group(1))


def find_line_index(lines: list[str], target: str) -> Optional[int]:
    target_lower = target.lower()
    for idx, line in enumerate(lines):
        if line.lower() == target_lower:
            return idx
    return None


def parse_header(lines: list[str]) -> tuple[Optional[str], Optional[str]]:
    for line in lines:
        match = re.search(r"Relatório\s*-\s*([^\d]+)\s+(\d{4})", line, re.IGNORECASE)
        if match:
            month_name = match.group(1).strip().lower()
            year = int(match.group(2))
            month_num = MONTH_MAP.get(month_name)
            if month_num:
                period = f"{year:04d}-{month_num:02d}"
                label = f"{month_name.capitalize()} {year}"
                return period, label
    return None, None


def parse_overall(lines: list[str]) -> Optional[dict]:
    views_idx = find_line_index(lines, "visualizações da página de destino")
    spend_idx = find_line_index(lines, "gastos")
    if views_idx is None or spend_idx is None:
        return None
    views = parse_number(lines[views_idx - 1]) if views_idx > 0 else None
    spend = parse_number(lines[spend_idx - 1]) if spend_idx > 0 else None
    if views is None or spend is None:
        return None
    cpv = round(spend / views, 4) if views else None
    return {
        "landingPageViews": views,
        "spend": spend,
        "currency": "EUR",
        "cpv": cpv,
    }


def parse_funnel(lines: list[str], name: str) -> dict:
    views_idx = find_line_index(lines, "visualizações da página de destino")
    spend_idx = find_line_index(lines, "gastos")
    cpv_idx = find_line_index(lines, "por visualização da página de destino")
    ctr_idx = find_line_index(lines, "CTR")

    views = parse_number(lines[views_idx - 1]) if views_idx is not None and views_idx > 0 else None
    spend = parse_number(lines[spend_idx - 1]) if spend_idx is not None and spend_idx > 0 else None
    cpv = parse_number(lines[cpv_idx - 1]) if cpv_idx is not None and cpv_idx > 0 else None
    ctr = parse_number(lines[ctr_idx - 1]) if ctr_idx is not None and ctr_idx > 0 else None

    return {
        "name": name,
        "landingPageViews": views,
        "spend": spend,
        "currency": "EUR",
        "cpv": cpv,
        "ctr": ctr,
    }


def parse_best_ads(lines: list[str]) -> list[dict]:
    ads: list[dict] = []
    current_name: Optional[str] = None
    for line in lines:
        line_lower = line.lower()
        if line_lower in IGNORE_LINES or "melhor performance" in line_lower:
            continue
        if "visualizações da página" in line_lower:
            views = parse_number_from_text(line)
            if current_name and views is not None:
                ads.append({"name": current_name, "landingPageViews": views})
            current_name = None
            continue
        current_name = line
    return ads


def parse_sold_cars(lines: list[str]) -> list[str]:
    cars: list[str] = []
    for line in lines:
        line_lower = line.lower()
        if line_lower in IGNORE_LINES or "carros vendidos" in line_lower:
            continue
        cars.append(line)
    return cars


def extract_report(path: Path) -> dict:
    reader = PdfReader(str(path))
    pages = reader.pages
    if not any((page.extract_text() or "").strip() for page in pages):
        return {
            "source": path.name,
            "period": None,
            "label": None,
            "status": "no_text",
            "notes": [
                "Text extraction failed; the PDF may be image-based. Provide OCR or a text-friendly version."
            ],
        }

    report: dict = {
        "source": path.name,
        "period": None,
        "label": None,
        "overall": None,
        "funnels": [],
        "soldCars": [],
        "status": "ok",
    }

    current_funnel: Optional[dict] = None
    for page in pages:
        text = page.extract_text() or ""
        if not text.strip():
            continue
        lines = [normalize_line(line) for line in text.splitlines() if line.strip()]
        period, label = parse_header(lines)
        if period and not report["period"]:
            report["period"] = period
            report["label"] = label

        if "Todas as campanhas" in lines:
            overall = parse_overall(lines)
            if overall:
                report["overall"] = overall

        funnel_name = None
        for line in lines:
            if line.lower().startswith("topo de funil -") or line.lower() == "remarketing":
                funnel_name = line
                break
        if funnel_name:
            funnel = parse_funnel(lines, funnel_name)
            report["funnels"].append(funnel)
            current_funnel = funnel
            continue

        if any("melhor performance" in line.lower() for line in lines):
            ads = parse_best_ads(lines)
            if current_funnel is None and report["funnels"]:
                current_funnel = report["funnels"][-1]
            if current_funnel is not None and ads:
                current_funnel.setdefault("bestAds", []).extend(ads)
            continue

        if any("carros vendidos" in line.lower() for line in lines):
            report["soldCars"].extend(parse_sold_cars(lines))

    return report


def refresh_ads_json(paths: Iterable[Path], output_path: Path) -> Optional[Path]:
    reports = [extract_report(path) for path in paths if path.exists()]
    if not reports:
        return None
    payload = {
        "generatedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "reports": reports,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return output_path


if __name__ == "__main__":
    pdf_paths = sorted(Path(".").glob("Relatório*Meta Ads*Autotrust*.pdf"))
    pdf_paths += sorted(Path(".").glob("Relatório*Meta Ads*Autotrust*.pdf"))
    output = Path("data/ads_reports.json")
    updated = refresh_ads_json(pdf_paths, output)
    if updated:
        print(f"Updated ads report JSON: {updated}")
    else:
        print("No ads report JSON updates performed.")
