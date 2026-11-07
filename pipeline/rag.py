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
# Personal medical advice: asking what *I* should do, how much, or how to treat someone. Historical questions
# ("What was sage used to treat?") are answered from the archive.
MEDICAL_RE = re.compile(
    r"\b(should|can|could|shall|may|do) i\b|\bis it safe|\brecommend|\bmy\b|\bi have\b"
    r"|\bdos(e|es|age|ing)\b|doz|how (much|many|often|long)|times (a|per) day"
    r"|\b(treat(ment)?|cure|heal)\s+(my|me|a|an|it|this|someone)\b|\btreatment\b"
    r"|sa herë|sa shumë|sa gjatë|trajt|kuro|shëro|mjeko|a duhet|si ta (marr|pi|përdor)|\bkam\b",
    re.I,
)
# Question words that say nothing about the plant; a passage must share at least one *other* word to be cited.
STOPWORDS = set("""
the and for which what who where when how does did are was were about say says said tell mention mentions
mentioned source sources archive archives text texts passage passages plant plants used use uses with from this
that these those any there their they them can could would should give show list find you your our its into
under code recipe recipes manuscript manuscripts name names called please know
çfarë cfare thonë thone thotë thote burimet burimi burim për per cilat cila cili bimët bimet bima bimë bime
arkiva arkivi arkivën arkiven rreth mbi dhe nga janë jane është eshte përdoret perdoret përdorur perdorur
""".split())
REFUSAL = "EthnoLens does not give medical advice, dosages or treatments. Uses in the archive are historical descriptions, not instructions."
NO_DATA = "The archive has no passage about this."
QUESTION_ALIASES = {
    "sherbela": ("sage", "sauge", "sal gemme"),
}

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


def _expand(question: str) -> str:
    """Add the historical spellings of plants the question names in English, Albanian or Latin.

    The passages are Middle English, so "sage" or "Sherbela" must also search for "sauge".
    """
    words = set(re.findall(r"[^\W\d_]{4,}", question.casefold()))
    aliases = [alias for word in words for alias in QUESTION_ALIASES.get(word, ())]
    names = set()
    with db.connect() as conn:
        for word in words:
            like = f"%{word}%"
            names.update(row[0] for row in conn.execute(
                "SELECT DISTINCT historical_name FROM records_full "
                "WHERE normalised_name LIKE ? OR local_name LIKE ? OR candidate_scientific_name LIKE ?",
                (like, like, like)))
    return " ".join([question, *aliases, *sorted(names)])


def _words(text: str) -> set[str]:
    return set(re.findall(r"[^\W\d_]{3,}", text.casefold()))


def _retrieve(question: str, limit: int = 5) -> list[dict[str, str]]:
    """Passages that contain at least one content word of the (expanded) question, most shared words first.

    Chroma always returns its nearest passages, even when none is about the question, and its HNSW search is
    approximate (it can skip a passage). So the candidates come from SQLite, a passage is cited only if it shares
    a word with the question (none -> no_data), and the Chroma ranking only breaks ties.
    """
    terms = _words(_expand(question)) - STOPWORDS
    if not terms:
        return []
    with db.connect() as conn:
        candidates = [dict(row) for row in conn.execute(
            """SELECT p.id AS passage_id, p.text AS passage, p.folio, d.source
               FROM passages p JOIN documents d ON d.id = p.document_id ORDER BY p.id"""
        )]
    scored = [(len(terms & _words(item["passage"])), item) for item in candidates]
    scored = [pair for pair in scored if pair[0] > 0]
    if not scored:
        return []
    rank: dict[str, int] = {}
    if chromadb is not None:
        index_passages()
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
        result = collection.query(query_embeddings=[_embedding(" ".join(sorted(terms)))],
                                  n_results=min(collection.count(), 100))
        rank = {meta["passage_id"]: i for i, meta in enumerate(result["metadatas"][0])}
    scored.sort(key=lambda pair: (-pair[0], rank.get(pair[1]["passage_id"], len(rank))))
    return [item for _, item in scored[:limit]]


def _generated_answer(question: str, passages: list[dict[str, str]]) -> str | None:
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        return None
    provider = os.getenv("LLM_PROVIDER", "openai").casefold()
    default_base = ("https://api.groq.com/openai/v1/chat/completions" if provider == "groq"
                    else "https://api.openai.com/v1/chat/completions")
    default_model = "llama-3.3-70b-versatile" if provider == "groq" else "gpt-4o-mini"
    context = "\n\n".join(
        f"[{item['source']}, {item['folio']}, {item['passage_id']}] {item['passage']}" for item in passages
    )
    try:
        response = requests.post(
            os.getenv("LLM_BASE_URL", default_base),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": os.getenv("LLM_MODEL", default_model), "temperature": 0,
                  "messages": [{"role": "system", "content": "Answer only from the supplied archive passages. Cite claims as [source, folio]. If the passages do not answer the question, say that the archive has no data."},
                               {"role": "user", "content": f"Question: {question}\n\nArchive passages:\n{context}"}]},
            timeout=90,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return None


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
