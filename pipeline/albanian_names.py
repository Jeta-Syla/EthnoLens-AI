"""Build data/processed/albanian_names.csv from Table 1 of Mustafa et al. (2012).

Source: Mustafa B, Hajdari A, Krasniqi F, et al. Medical ethnobotany of the Albanian Alps in Kosovo.
J Ethnobiol Ethnomed. 2012;8:6. https://doi.org/10.1186/1746-4269-8-6 (CC BY 2.0)

One CSV row per (species, Albanian folk name), with columns matching the `plant_names` table
plus scientific_name, family and english_name for reference.

Usage (from the repo root):
  python -m pipeline.albanian_names
"""

import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "data" / "processed" / "albanian_names.csv"

FULLTEXT_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3285519/fullTextXML"
HEADERS = {"User-Agent": "EthnoLens-AI/0.1 (student research prototype)"}

SOURCE = "Mustafa et al. 2012"
REGION = "Albanian Alps, Kosovo"
FIELDS = ["canonical_name", "local_name", "language", "region", "source",
          "scientific_name", "family", "english_name"]

FAMILY_RE = re.compile(r"\(([A-Z][a-z]+(?:aceae|ae))\)")
VOUCHER_RE = re.compile(r"\s*\d+/DE/?\d+")  # herbarium voucher number, e.g. "65/DE/10"


def _text(el: ET.Element) -> str:
    return " ".join("".join(el.itertext()).split())


def _cell_lines(td: ET.Element) -> list[str]:
    """Split a cell on <break/> into its separate names."""
    lines, current = [], [td.text or ""]
    for child in td:
        if child.tag == "break":
            lines.append("".join(current))
            current = [child.tail or ""]
        else:
            current.append("".join(child.itertext()) + (child.tail or ""))
    lines.append("".join(current))
    return [" ".join(line.split()) for line in lines if line.strip()]


def parse_table(xml: str) -> list[dict]:
    root = ET.fromstring(xml)
    table = next(tw for tw in root.iter("table-wrap") if tw.get("id") == "T1")
    rows = []
    for tr in table.iter("tr"):
        cells = tr.findall("td")
        if not cells or not _text(cells[0]):
            continue  # header row or a continuation row of the previous species
        taxon = VOUCHER_RE.sub("", _text(cells[0]))
        family = FAMILY_RE.search(taxon)
        italics = " ".join(_text(i) for i in cells[0].iter("italic"))
        for local_name in _cell_lines(cells[1]):
            rows.append({
                "canonical_name": " ".join(italics.split()),
                "local_name": local_name,
                "language": "Albanian",
                "region": REGION,
                "source": SOURCE,
                "scientific_name": taxon[:family.start()].strip() if family else taxon,
                "family": family.group(1) if family else "",
                "english_name": _text(cells[2]),
            })
    return rows


def main() -> None:
    resp = requests.get(FULLTEXT_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    rows = parse_table(resp.content.decode("utf-8"))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    species = len({r["canonical_name"] for r in rows})
    print(f"{len(rows)} names for {species} species -> {OUT_PATH}")


if __name__ == "__main__":
    main()
