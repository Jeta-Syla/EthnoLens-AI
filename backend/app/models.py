"""Pydantic models for the API.

`Record` mirrors schema/record.json: every key is required, unknown values are None.
If you change one, change the other and tell the team first.
"""

import json
import sqlite3
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt

EvidenceType = Literal["stated", "inferred"]


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plant: EvidenceType
    scientific_name: EvidenceType


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^rec_[0-9]{4,}$")
    historical_name: str = Field(min_length=1)
    normalised_name: str | None
    local_name: str | None
    candidate_scientific_name: str | None
    plant_part: str | None
    preparation: str | None
    described_use: str | None
    other_ingredients: list[str]
    source: str = Field(min_length=1)
    folio: str = Field(min_length=1)
    passage: str = Field(min_length=1)
    span: tuple[NonNegativeInt, NonNegativeInt] | None
    language: str | None
    region: str | None
    period: str | None
    evidence: Evidence
    extraction_confidence: float = Field(ge=0, le=1)
    mapping_confidence: Literal["high", "medium", "candidate"] | None
    review_status: Literal["pending", "verified", "rejected"]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Record":
        """Build a Record from a row of the `records_full` view."""
        data = dict(row)
        start, end = data.pop("span_start"), data.pop("span_end")
        data["span"] = (start, end) if start is not None and end is not None else None
        data["other_ingredients"] = json.loads(data["other_ingredients"])
        data["evidence"] = json.loads(data["evidence"])
        return cls(**data)


class Document(BaseModel):
    """A source document, as stored in the `documents` table."""

    id: str
    source: str
    collection: Literal["curious_cures", "bhl", "field_study", "upload"]
    title: str | None = None
    url: str | None = None
    language: str | None = None
    period: str | None = None
    region: str | None = None
    licence: str | None = None


class Passage(BaseModel):
    """One page/folio of text, as stored in the `passages` table."""

    id: str
    document_id: str
    folio: str
    seq: int = 0
    text: str = Field(min_length=1)
    method: Literal["transcription", "ocr", "manual"]


class UploadResult(BaseModel):
    """Response of POST /documents: what was stored, and the records extracted so far."""

    document: Document
    passages: list[Passage]
    records: list[Record]


class Health(BaseModel):
    status: Literal["ok"]
    database: Literal["ok"]
