"""EthnoLens AI API.

Run from the repo root:
  uvicorn backend.app.main:app --reload
Docs at http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app import db
from backend.app.models import Health


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
