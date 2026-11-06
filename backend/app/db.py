"""SQLite storage for EthnoLens AI.

Four tables:
  documents    one row per source (a manuscript, a BHL book, an upload)
  passages     the text of one folio/page of a document
  records      one extracted plant mention, linked to the passage it came from
  plant_names  local/vernacular names per scientific name (e.g. Mustafa et al. 2012)

The view `records_full` joins them back into the flat shape of schema/record.json,
so the API can return contract records directly.

Run `python -m backend.app.db` from the repo root to create the database.
"""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.environ.get("ETHNOLENS_DB", REPO_ROOT / "data" / "ethnolens.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,             -- e.g. "MS-ADD-09308", "bhl-12345"
    source      TEXT NOT NULL,                -- citation shown to users, e.g. "MS Add. 9308"
    collection  TEXT NOT NULL CHECK (collection IN ('curious_cures', 'bhl', 'field_study', 'upload')),
    title       TEXT,
    url         TEXT,
    language    TEXT,                         -- e.g. "Middle English", "Latin"
    period      TEXT,                         -- free text, e.g. "c. 1400"
    region      TEXT,
    licence     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS passages (
    id           TEXT PRIMARY KEY,
    document_id  TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    folio        TEXT NOT NULL,               -- IIIF page label ("2r") or BHL page number
    seq          INTEGER NOT NULL DEFAULT 0,  -- order of the passage within the document
    text         TEXT NOT NULL,               -- exact transcription / OCR text, spelling preserved
    method       TEXT NOT NULL CHECK (method IN ('transcription', 'ocr', 'manual')),
    UNIQUE (document_id, folio, seq)
);

CREATE TABLE IF NOT EXISTS records (
    id                         TEXT PRIMARY KEY,    -- e.g. "rec_0001"
    passage_id                 TEXT NOT NULL REFERENCES passages(id) ON DELETE CASCADE,
    historical_name            TEXT NOT NULL,       -- exactly as written in the passage
    normalised_name            TEXT,
    candidate_scientific_name  TEXT,                -- as returned by GBIF, with author ("Salvia officinalis L.")
    canonical_name             TEXT,                -- without author ("Salvia officinalis"), used to join plant_names
    plant_part                 TEXT,
    preparation                TEXT,
    described_use              TEXT,
    other_ingredients          TEXT NOT NULL DEFAULT '[]',  -- JSON array
    span_start                 INTEGER,             -- character offsets of historical_name in passages.text
    span_end                   INTEGER,
    evidence                   TEXT NOT NULL DEFAULT '{}',  -- JSON object, e.g. {"plant": "stated", "scientific_name": "inferred"}
    extraction_confidence      REAL CHECK (extraction_confidence BETWEEN 0 AND 1),
    mapping_confidence         TEXT CHECK (mapping_confidence IN ('high', 'medium', 'candidate')),
    review_status              TEXT NOT NULL DEFAULT 'pending'
                               CHECK (review_status IN ('pending', 'verified', 'rejected')),
    created_at                 TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (span_start IS NULL OR span_end IS NULL OR span_start <= span_end)
);

CREATE TABLE IF NOT EXISTS plant_names (
    id              INTEGER PRIMARY KEY,
    canonical_name  TEXT NOT NULL,            -- scientific name without author
    local_name      TEXT NOT NULL,            -- e.g. "Sherbela"
    language        TEXT NOT NULL DEFAULT 'Albanian',
    region          TEXT,                     -- e.g. "Albanian Alps, Kosovo"
    source          TEXT NOT NULL,            -- e.g. "Mustafa et al. 2012"
    UNIQUE (canonical_name, local_name, region, source)
);

CREATE INDEX IF NOT EXISTS idx_passages_document ON passages(document_id);
CREATE INDEX IF NOT EXISTS idx_records_passage   ON records(passage_id);
CREATE INDEX IF NOT EXISTS idx_records_canonical ON records(canonical_name);
CREATE INDEX IF NOT EXISTS idx_plant_names_canon ON plant_names(canonical_name);

-- Flat view matching schema/record.json. local_name is the first documented local name, if any.
CREATE VIEW IF NOT EXISTS records_full AS
SELECT
    r.id,
    r.historical_name,
    r.normalised_name,
    (SELECT pn.local_name FROM plant_names pn
      WHERE pn.canonical_name = r.canonical_name
      ORDER BY pn.id LIMIT 1)          AS local_name,
    r.candidate_scientific_name,
    r.plant_part,
    r.preparation,
    r.described_use,
    r.other_ingredients,
    d.source,
    p.folio,
    p.text                             AS passage,
    r.span_start,
    r.span_end,
    d.language,
    d.region,
    d.period,
    r.evidence,
    r.extraction_confidence,
    r.mapping_confidence,
    r.review_status
FROM records r
JOIN passages  p ON p.id = r.passage_id
JOIN documents d ON d.id = p.document_id;
"""


@contextmanager
def connect(path: Path | str = DB_PATH) -> Iterator[sqlite3.Connection]:
    """`with connect() as conn:` commits on success, rolls back on error, and always closes.

    (sqlite3's own `with` only commits; an open connection keeps the file locked on Windows.)
    """
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(path: Path | str = DB_PATH) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA)


# Upserts never delete rows, so records already extracted from a passage are kept on reload.
# (INSERT OR REPLACE would delete the old row and cascade-delete its records.)

def upsert_document(conn: sqlite3.Connection, document: dict) -> None:
    conn.execute(
        """INSERT INTO documents (id, source, collection, title, url, language, period, region, licence)
           VALUES (:id, :source, :collection, :title, :url, :language, :period, :region, :licence)
           ON CONFLICT(id) DO UPDATE SET source=excluded.source, title=excluded.title, url=excluded.url,
             language=excluded.language, period=excluded.period, region=excluded.region,
             licence=excluded.licence""",
        {"title": None, "url": None, "language": None, "period": None, "region": None, "licence": None,
         **document},
    )


def upsert_passages(conn: sqlite3.Connection, passages: list[dict]) -> None:
    conn.executemany(
        """INSERT INTO passages (id, document_id, folio, seq, text, method)
           VALUES (:id, :document_id, :folio, :seq, :text, :method)
           ON CONFLICT(id) DO UPDATE SET folio=excluded.folio, seq=excluded.seq, text=excluded.text,
             method=excluded.method""",
        passages,
    )


def upsert_records(conn: sqlite3.Connection, records: list[dict]) -> None:
    """Store validated extraction results while preserving passage traceability."""
    conn.executemany(
        """INSERT INTO records (
               id, passage_id, historical_name, normalised_name,
               candidate_scientific_name, canonical_name, plant_part,
               preparation, described_use, other_ingredients, span_start,
               span_end, evidence, extraction_confidence, mapping_confidence,
               review_status
           ) VALUES (
               :id, :passage_id, :historical_name, :normalised_name,
               :candidate_scientific_name, :canonical_name, :plant_part,
               :preparation, :described_use, :other_ingredients, :span_start,
               :span_end, :evidence, :extraction_confidence,
               :mapping_confidence, :review_status
           )
           ON CONFLICT(id) DO UPDATE SET
               passage_id=excluded.passage_id,
               historical_name=excluded.historical_name,
               normalised_name=excluded.normalised_name,
               candidate_scientific_name=excluded.candidate_scientific_name,
               canonical_name=excluded.canonical_name,
               plant_part=excluded.plant_part,
               preparation=excluded.preparation,
               described_use=excluded.described_use,
               other_ingredients=excluded.other_ingredients,
               span_start=excluded.span_start,
               span_end=excluded.span_end,
               evidence=excluded.evidence,
               extraction_confidence=excluded.extraction_confidence,
               mapping_confidence=excluded.mapping_confidence,
               review_status=excluded.review_status""",
        records,
    )


if __name__ == "__main__":
    init_db()
    print(f"Database ready: {DB_PATH}")
