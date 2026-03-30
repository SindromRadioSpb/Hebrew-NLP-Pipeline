# kadima/api/routers/corpora.py
"""REST API: Corpus management endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from typing import List

from kadima.api.schemas import CorpusCreate, CorpusResponse
from kadima.data.db import ensure_db, get_connection

logger = logging.getLogger(__name__)

router = APIRouter()

DB_PATH = "~/.kadima/kadima.db"


@router.get("/corpora", response_model=List[CorpusResponse])
async def list_corpora():
    """List all active corpora."""
    logger.info("Listing active corpora")
    ensure_db(DB_PATH)
    conn = get_connection(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT * FROM corpora WHERE status='active' ORDER BY created_at DESC"
        ).fetchall()
        return [
            CorpusResponse(
                id=r["id"], name=r["name"], language=r["language"],
                created_at=str(r["created_at"]), status=r["status"],
            )
            for r in rows
        ]
    finally:
        conn.close()


@router.post("/corpora", response_model=CorpusResponse, status_code=201)
async def create_corpus(body: CorpusCreate):
    """Create a new corpus."""
    logger.info("Creating corpus: %s (lang=%s)", body.name, body.language)
    ensure_db(DB_PATH)
    conn = get_connection(DB_PATH)
    try:
        cur = conn.execute(
            "INSERT INTO corpora (name, language) VALUES (?, ?)",
            (body.name, body.language),
        )
        conn.commit()
        corpus_id = cur.lastrowid
        row = conn.execute("SELECT * FROM corpora WHERE id=?", (corpus_id,)).fetchone()
        return CorpusResponse(
            id=row["id"], name=row["name"], language=row["language"],
            created_at=str(row["created_at"]), status=row["status"],
        )
    finally:
        conn.close()


@router.get("/corpora/{corpus_id}", response_model=CorpusResponse)
async def get_corpus(corpus_id: int):
    """Get corpus details by ID."""
    logger.info("Getting corpus %d", corpus_id)
    ensure_db(DB_PATH)
    conn = get_connection(DB_PATH)
    try:
        row = conn.execute("SELECT * FROM corpora WHERE id=?", (corpus_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Corpus not found")
        return CorpusResponse(
            id=row["id"], name=row["name"], language=row["language"],
            created_at=str(row["created_at"]), status=row["status"],
        )
    finally:
        conn.close()


@router.delete("/corpora/{corpus_id}", status_code=204)
async def delete_corpus(corpus_id: int):
    """Soft-delete a corpus (set status=archived)."""
    logger.info("Deleting corpus %d", corpus_id)
    ensure_db(DB_PATH)
    conn = get_connection(DB_PATH)
    try:
        conn.execute("UPDATE corpora SET status='archived' WHERE id=?", (corpus_id,))
        conn.commit()
    finally:
        conn.close()
