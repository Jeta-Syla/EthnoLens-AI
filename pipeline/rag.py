"""Retrieval-augmented answers grounded in the archive passages."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

from backend.app import db

load_dotenv(db.REPO_ROOT / ".env")

CHROMA_DIR = Path(os.getenv("ETHNOLENS_CHROMA", db.REPO_ROOT / "data" / "chroma"))
COLLECTION = "ethnolens_passages"
MEDICAL_RE = re.compile(r"doz|sa herë|trajtim|a duhet ta marr|dosage|dose|treatment|should i take|how many times", re.I)
REFUSAL = "EthnoLens does not give medical advice, dosages or treatments. Uses in the archive are historical descriptions, not instructions."
NO_DATA = "The archive has no passage about this."

try:
    import chromadb
except ModuleNotFoundError:  # The API can still use the SQL search fallback.
    chromadb = None


def _embedding(text: str) -> list[float]:
    """Create a deterministic local embedding without downloading a model."""
    vector = [0.0] * 128
    words = re.findall(r"[^\W\d_]{2,}", text.casefold())
    for word in words:
        digest = hashlib.sha256(word.encode()).digest()
        index = int.from_bytes(digest[:2], "big") % len(vector)
        vector[index] += 1.0
    norm = sum(value * value for value in vector) ** 0.5 or 1.0
    return [value / norm for value in vector]


def index_passages() -> int:
    """Upsert every stored passage into the persistent Chroma collection."""
    db.init_db()
    if chromadb is None:
        with db.connect() as conn:
            return conn.execute("SELECT count(*) FROM passages").fetchone()[0]
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT p.id, p.text, p.folio, d.source
               FROM passages p JOIN documents d ON d.id = p.document_id
               ORDER BY p.id"""
        ).fetchall()
    if rows:
        collection.upsert(
            ids=[row["id"] for row in rows],
            documents=[row["text"] for row in rows],
            embeddings=[_embedding(row["text"]) for row in rows],
            metadatas=[{"source": row["source"], "folio": row["folio"], "passage_id": row["id"]} for row in rows],
        )
    return len(rows)


def _retrieve(question: str, limit: int = 5) -> list[dict[str, str]]:
    if chromadb is None:
        words = set(re.findall(r"[^\W\d_]{3,}", question.casefold()))
        with db.connect() as conn:
            rows = conn.execute(
                """SELECT p.id AS passage_id, p.text AS passage, p.folio, d.source
                   FROM passages p JOIN documents d ON d.id = p.document_id"""
            ).fetchall()
        ranked = sorted(rows, key=lambda row: -sum(word in row["passage"].casefold() for word in words))
        return [dict(row) for row in ranked[:limit] if any(word in row["passage"].casefold() for word in words)]
    index_passages()
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    if collection.count() == 0:
        return []
    result = collection.query(query_embeddings=[_embedding(question)], n_results=min(limit, collection.count()))
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    return [{"passage": text, **metadata} for text, metadata in zip(documents, metadatas)]


def _generated_answer(question: str, passages: list[dict[str, str]]) -> str | None:
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        return None
    context = "\n\n".join(
        f"[{item['source']}, {item['folio']}, {item['passage_id']}] {item['passage']}" for item in passages
    )
    response = requests.post(
        os.getenv("LLM_BASE_URL", "https://api.openai.com/v1/chat/completions"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": os.getenv("LLM_MODEL", "gpt-4o-mini"), "temperature": 0,
              "messages": [{"role": "system", "content": "Answer only from the supplied archive passages. Cite claims as [source, folio]. If the passages do not answer the question, say that the archive has no data."},
                           {"role": "user", "content": f"Question: {question}\n\nArchive passages:\n{context}"}]},
        timeout=90,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def answer(question: str) -> dict:
    """Return the API's answer/citations/mode shape."""
    if MEDICAL_RE.search(question):
        return {"answer": REFUSAL, "citations": [], "mode": "refused"}
    passages = _retrieve(question)
    if not passages:
        return {"answer": NO_DATA, "citations": [], "mode": "no_data"}
    citations = [{"source": item["source"], "folio": item["folio"],
                  "passage": item["passage"], "passage_id": item["passage_id"]} for item in passages]
    generated = _generated_answer(question, passages)
    if generated:
        return {"answer": generated, "citations": citations, "mode": "rag"}
    return {"answer": f"{len(citations)} relevant passage(s) found in the archive. Open a citation to read the source.",
            "citations": citations, "mode": "search"}
