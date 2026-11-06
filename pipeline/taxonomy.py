"""Map candidate scientific names to GBIF and score how sure the match is.

The LLM proposes a Latin name for each historical plant name (records.candidate_scientific_name).
GBIF's species match (v2, kingdom Plantae) then checks it:

  EXACT match, confidence >= 90, rank species or lower             -> high
  VARIANT/FUZZY match, or EXACT below 90, rank species or lower    -> medium
  anything else (genus/kingdom only, no match)                     -> candidate

A synonym is replaced by its accepted name, but only after an EXACT match: a near-miss that lands
on a synonym is two guesses in a row (e.g. "Artemisia absinthum" -> A. absinthii -> A. pallens),
so it stays a candidate.

canonical_name is the join key with plant_names, so it is kept at species level (genus + epithet):
GBIF may accept a subspecies, e.g. Betula verrucosa -> Betula pendula subsp. pendula. A "candidate" keeps the LLM's name, is never
presented as an identification, and gets no canonical_name, so it is not joined to local names.

Usage (from the repo root):
  python -m pipeline.taxonomy                         # map every record not mapped yet
  python -m pipeline.taxonomy --name "Salvia officinalis"
"""

import argparse
import json
from functools import lru_cache

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.app import db

MATCH_URL = "https://api.gbif.org/v2/species/match"
HEADERS = {"User-Agent": "EthnoLens-AI/0.1 (student research prototype)"}

# GBIF occasionally drops a connection; retry a few times with backoff before giving up.
_session = requests.Session()
_session.headers.update(HEADERS)
_session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=4, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET",))))
SPECIES_RANKS = {"SPECIES", "SUBSPECIES", "VARIETY", "FORM"}
HIGH_CONFIDENCE = 90


@lru_cache(maxsize=None)
def match(name: str) -> dict:
    """GBIF match for one name: scientific name, canonical name and mapping confidence."""
    resp = _session.get(MATCH_URL, timeout=30, params={"scientificName": name, "kingdom": "Plantae"})
    resp.raise_for_status()
    data = resp.json()
    diagnostics = data.get("diagnostics", {})
    match_type = diagnostics.get("matchType", "NONE")
    confidence = diagnostics.get("confidence", 0)
    usage = data.get("acceptedUsage") or data.get("usage") or {}

    near_miss_synonym = match_type != "EXACT" and data.get("synonym")
    if match_type not in ("EXACT", "VARIANT", "FUZZY") or usage.get("rank") not in SPECIES_RANKS or near_miss_synonym:
        return {"candidate_scientific_name": name, "canonical_name": None,
                "mapping_confidence": "candidate", "gbif_key": None,
                "match_type": match_type, "gbif_confidence": confidence}

    level = "high" if match_type == "EXACT" and confidence >= HIGH_CONFIDENCE else "medium"
    species = " ".join(usage["canonicalName"].split()[:2])
    return {"candidate_scientific_name": usage["name"], "canonical_name": species,
            "mapping_confidence": level, "gbif_key": usage.get("key"),
            "match_type": match_type, "gbif_confidence": confidence}


def map_records() -> int:
    """Map every record that has a proposed name but no mapping confidence yet."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, candidate_scientific_name FROM records "
            "WHERE candidate_scientific_name IS NOT NULL AND mapping_confidence IS NULL"
        ).fetchall()
        for row in rows:
            result = match(row["candidate_scientific_name"])
            conn.execute(
                "UPDATE records SET candidate_scientific_name = ?, canonical_name = ?, mapping_confidence = ? "
                "WHERE id = ?",
                (result["candidate_scientific_name"], result["canonical_name"],
                 result["mapping_confidence"], row["id"]),
            )
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Map candidate scientific names to GBIF.")
    parser.add_argument("--name", help="match a single name and print the result")
    args = parser.parse_args()
    if args.name:
        print(json.dumps(match(args.name), ensure_ascii=False, indent=2))
    else:
        print(f"{map_records()} records mapped")


if __name__ == "__main__":
    main()
