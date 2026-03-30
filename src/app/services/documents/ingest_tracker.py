"""
@file ingest_tracker.py
@author naflashDev
@brief Simple SQLite tracker to record ingested documents and avoid duplicates
@details Provides a tiny persistence layer that stores the content hash, computed
doc_id, stored path, filename, folder, timestamp and whether the document was
successfully upserted into the vectorstore. The worker/ingest service can query
this tracker to skip already-ingested files or retry indexing for failed items.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict

DB_PATH = Path('data') / 'documents' / 'ingest_index.db'

# Prefer using the conversation DB (SQLAlchemy) when available so records
# live in the same `conversations.db` file. Fall back to a lightweight
# per-folder SQLite DB if the SQLAlchemy models are not importable.
try:
    from app.models.conversation_db import SessionLocal
    from app.models.ingested_document import IngestedDocument
    _USE_SQLA = True
except Exception:
    _USE_SQLA = False


def _ensure_db():
    """
    Ensure the SQLite DB and table exist.

    Returns a sqlite3.Connection object.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ingested_docs (
            content_hash TEXT PRIMARY KEY,
            doc_id TEXT,
            stored_path TEXT,
            filename TEXT,
            folder TEXT,
            timestamp TEXT,
            upserted INTEGER
        )
        """
    )
    conn.commit()
    return conn


def _record_sqlalchemy(content_hash: str, doc_id: str, stored_path: str | None, filename: str | None, folder: str | None, upserted: bool = False):
    db = SessionLocal()
    try:
        obj = db.get(IngestedDocument, content_hash)
        if obj is None:
            obj = IngestedDocument(content_hash=content_hash, doc_id=doc_id, stored_path=stored_path, filename=filename, folder=folder, upserted=bool(upserted))
            db.add(obj)
        else:
            obj.doc_id = doc_id
            obj.stored_path = stored_path
            obj.filename = filename
            obj.folder = folder
            obj.upserted = bool(upserted)
        db.commit()
    finally:
        db.close()


def _exists_sqlalchemy(content_hash: str) -> bool:
    db = SessionLocal()
    try:
        obj = db.get(IngestedDocument, content_hash)
        return obj is not None
    finally:
        db.close()


def _get_sqlalchemy(content_hash: str) -> Optional[Dict]:
    db = SessionLocal()
    try:
        obj = db.get(IngestedDocument, content_hash)
        if not obj:
            return None
        return {
            'content_hash': obj.content_hash,
            'doc_id': obj.doc_id,
            'stored_path': obj.stored_path,
            'filename': obj.filename,
            'folder': obj.folder,
            'timestamp': obj.timestamp.isoformat() if obj.timestamp else None,
            'upserted': bool(obj.upserted)
        }
    finally:
        db.close()


def _mark_upserted_sqlalchemy(content_hash: str):
    db = SessionLocal()
    try:
        obj = db.get(IngestedDocument, content_hash)
        if obj:
            obj.upserted = True
            db.commit()
    finally:
        db.close()


def record_ingest(content_hash: str, doc_id: str, stored_path: str | None, filename: str | None, folder: str | None, upserted: bool = False):
    """
    Record or update an ingestion entry.

    content_hash: SHA256 hex of file bytes (primary key).
    """
    if _USE_SQLA:
        try:
            _record_sqlalchemy(content_hash, doc_id, stored_path, filename, folder, upserted=upserted)
            return
        except Exception:
            # Fallthrough to sqlite fallback on errors
            pass
    conn = _ensure_db()
    cur = conn.cursor()
    ts = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "INSERT OR REPLACE INTO ingested_docs (content_hash, doc_id, stored_path, filename, folder, timestamp, upserted) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (content_hash, doc_id, stored_path or '', filename or '', folder or '', ts, 1 if upserted else 0),
    )
    conn.commit()
    try:
        conn.close()
    except Exception:
        pass


def exists_by_hash(content_hash: str) -> bool:
    """Return True if an entry with this content_hash exists."""
    if _USE_SQLA:
        try:
            return _exists_sqlalchemy(content_hash)
        except Exception:
            pass
    conn = _ensure_db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM ingested_docs WHERE content_hash=? LIMIT 1", (content_hash,))
    res = cur.fetchone()
    try:
        conn.close()
    except Exception:
        pass
    return bool(res)


def get_entry(content_hash: str) -> Optional[Dict]:
    """Return the DB row as a dict or None if not found."""
    if _USE_SQLA:
        try:
            return _get_sqlalchemy(content_hash)
        except Exception:
            pass
    conn = _ensure_db()
    cur = conn.cursor()
    cur.execute("SELECT content_hash, doc_id, stored_path, filename, folder, timestamp, upserted FROM ingested_docs WHERE content_hash=?", (content_hash,))
    row = cur.fetchone()
    try:
        conn.close()
    except Exception:
        pass
    if not row:
        return None
    return {
        'content_hash': row[0],
        'doc_id': row[1],
        'stored_path': row[2],
        'filename': row[3],
        'folder': row[4],
        'timestamp': row[5],
        'upserted': bool(row[6])
    }


def mark_upserted(content_hash: str):
    """Mark an existing entry as upserted (vector indexed)."""
    if _USE_SQLA:
        try:
            _mark_upserted_sqlalchemy(content_hash)
            return
        except Exception:
            pass
    conn = _ensure_db()
    cur = conn.cursor()
    cur.execute("UPDATE ingested_docs SET upserted=1 WHERE content_hash=?", (content_hash,))
    conn.commit()
    try:
        conn.close()
    except Exception:
        pass
