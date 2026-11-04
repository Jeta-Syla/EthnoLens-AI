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
from backend.app.models import Document, Health, Passage, Record, UploadResult

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


def _extract(passages: list[Passage]) -> None:
    """Run the extraction pipeline on new passages, once pipeline/extract.py provides it.

    Expected: extract_passage(passage: Passage) -> None, which validates and writes records to the database.
    """
    try:
        from pipeline.extract import extract_passage
    except ImportError:
        return
    for passage in passages:
        extract_passage(passage)


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

    _extract(passages)

    with db.connect() as conn:
        rows = conn.execute(
            """SELECT rf.* FROM records_full rf
               JOIN records r ON r.id = rf.id
               JOIN passages p ON p.id = r.passage_id
               WHERE p.document_id = ? ORDER BY rf.id""",
            (doc_id,),
        ).fetchall()
    return UploadResult(document=document, passages=passages, records=[Record.from_row(r) for r in rows])
