"""EthnoLens AI API.

Run from the repo root:
  uvicorn backend.app.main:app --reload
Docs at http://localhost:8000/docs
"""

import io
import tempfile
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile

from backend.app import db
from backend.app.models import (AskRequest, AskResponse, Document, Health, LocalName, MapPoint, PlantPage,
                                Passage, Record, UploadResult)

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="EthnoLens AI API", version="0.1.0", lifespan=lifespan)


@app.get("/health", response_model=Health)
def health() -> Health:
    with db.connect() as conn:
        conn.execute("SELECT 1")
    return Health(status="ok", database="ok")


@app.get("/records", response_model=list[Record])
def list_records(
    q: str | None = Query(None, description="Search in plant names and passage text"),
    plant_part: str | None = None,
    preparation: str | None = None,
    source: str | None = None,
    language: str | None = None,
    review_status: Literal["pending", "verified", "rejected"] | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[Record]:
    where, params = [], []
    if q:
        where.append("(historical_name LIKE ? OR normalised_name LIKE ? OR local_name LIKE ?"
                     " OR candidate_scientific_name LIKE ? OR passage LIKE ?)")
        params += [f"%{q}%"] * 5
    for column, value in [("plant_part", plant_part), ("preparation", preparation), ("source", source),
                          ("language", language), ("review_status", review_status)]:
        if value is not None:
            where.append(f"{column} = ?")
            params.append(value)
    sql = "SELECT * FROM records_full"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id LIMIT ? OFFSET ?"
    with db.connect() as conn:
        rows = conn.execute(sql, [*params, limit, offset]).fetchall()
    return [Record.from_row(row) for row in rows]


@app.get("/plants/{canonical_name}", response_model=PlantPage)
def plant_page(canonical_name: str) -> PlantPage:
    """All archive mentions of one species (GBIF canonical name, e.g. "Salvia officinalis") and its local names."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT rf.* FROM records_full rf JOIN records r ON r.id = rf.id "
            "WHERE r.canonical_name = ? ORDER BY rf.source, rf.folio, rf.id",
            (canonical_name,),
        ).fetchall()
        names = conn.execute(
            "SELECT local_name, language, region, source FROM plant_names WHERE canonical_name = ? ORDER BY id",
            (canonical_name,),
        ).fetchall()
    if not rows and not names:
        raise HTTPException(404, f"No records or local names for '{canonical_name}'")
    return PlantPage(canonical_name=canonical_name, local_names=[LocalName(**dict(n)) for n in names],
                     records=[Record.from_row(r) for r in rows])


@app.get("/map", response_model=list[MapPoint])
def map_points() -> list[MapPoint]:
    """Documented local names with their region. Only documented sources: no region, no point."""
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT pn.region, pn.local_name, pn.canonical_name AS scientific_name, pn.source,
                      (SELECT count(*) FROM records r WHERE r.canonical_name = pn.canonical_name) AS in_archive
               FROM plant_names pn WHERE pn.region IS NOT NULL
               ORDER BY in_archive DESC, pn.local_name"""
        ).fetchall()
    return [MapPoint(**dict(r)) for r in rows]


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """Answer only from archive passages, with citations (pipeline/rag.py). Medical questions are refused there."""
    from pipeline.rag import answer

    return AskResponse(**answer(request.question))


def _read_pages(data: bytes, suffix: str, ocr_lang: str) -> list[tuple[str, str]]:
    """Return (text, method) per page of an uploaded file."""
    if suffix == ".txt":
        return [(data.decode("utf-8"), "manual")]

    import pytesseract
    from PIL import Image

    from pipeline.ocr import ocr_image, ocr_pdf

    try:
        if suffix in IMAGE_SUFFIXES:
            return [(ocr_image(Image.open(io.BytesIO(data)), ocr_lang), "ocr")]
        if suffix == ".pdf":
            from pdf2image.exceptions import PDFInfoNotInstalledError

            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "upload.pdf"
                path.write_bytes(data)
                try:
                    return [(text, "ocr") for _, text in ocr_pdf(path, ocr_lang)]
                except PDFInfoNotInstalledError:
                    raise HTTPException(503, "PDF upload needs Poppler installed on the server")
    except pytesseract.TesseractNotFoundError:
        raise HTTPException(503, "OCR needs Tesseract installed on the server")
    raise HTTPException(415, f"Unsupported file type '{suffix}'. Use .txt, .pdf or an image.")


def _extract(passages: list[Passage]) -> list[str]:
    """Extract records from new passages (pipeline/extract.py), then map them to GBIF.

    The upload never fails because of the LLM or GBIF: the text is stored either way, and the returned
    notes say what could not be done.
    """
    import requests

    from pipeline.extract import extract_passage
    from pipeline.taxonomy import map_records

    notes = []
    for passage in passages:
        try:
            extract_passage(passage)
        except Exception as error:  # missing API key, network error, or an invalid model response
            notes.append(f"Extraction skipped for {passage.folio}: {error}")
    try:
        from pipeline.propose_names import propose

        propose([passage.id for passage in passages])  # candidate Latin names, checked by GBIF below
    except Exception as error:  # the upload never fails because of this step
        notes.append(f"Scientific names not proposed: {error}")
    try:
        map_records()
    except requests.RequestException:
        notes.append("GBIF is unreachable; scientific names will be mapped on the next run.")
    return notes


@app.post("/documents", response_model=UploadResult, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    language: str | None = Form(None),
    period: str | None = Form(None),
    ocr_lang: str = Form("eng", description="Tesseract language, e.g. eng"),
) -> UploadResult:
    filename = file.filename or "upload"
    pages = [(text.strip(), method) for text, method in _read_pages(file.file.read(), Path(filename).suffix.lower(), ocr_lang)]
    pages = [(n, text, method) for n, (text, method) in enumerate(pages, start=1) if text]
    if not pages:
        raise HTTPException(422, "No text found in the uploaded file")

    doc_id = f"upload-{uuid.uuid4().hex[:8]}"
    document = Document(id=doc_id, source=title or filename, collection="upload",
                        title=title, language=language, period=period)
    passages = [Passage(id=f"{doc_id}:p{n}", document_id=doc_id, folio=f"p. {n}", seq=n, text=text, method=method)
                for n, text, method in pages]

    with db.connect() as conn:
        db.upsert_document(conn, document.model_dump())
        db.upsert_passages(conn, [p.model_dump() for p in passages])

    notes = _extract(passages)

    with db.connect() as conn:
        rows = conn.execute(
            """SELECT rf.* FROM records_full rf
               JOIN records r ON r.id = rf.id
               JOIN passages p ON p.id = r.passage_id
               WHERE p.document_id = ? ORDER BY rf.id""",
            (doc_id,),
        ).fetchall()
    return UploadResult(document=document, passages=passages, records=[Record.from_row(r) for r in rows],
                        notes=notes)
