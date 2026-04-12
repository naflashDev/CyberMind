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

# Detect whether Chroma is available at module import time. If Chroma is
# available we prefer to rely on its metadata for deduplication and avoid
# creating a local ingest_index.db unless explicitly needed.
try:
    import chromadb  # type: ignore
    _CHROMA_AVAILABLE_FOR_TRACKER = True
except Exception:
    _CHROMA_AVAILABLE_FOR_TRACKER = False

# Local DB is enabled only when Chroma is not available. This prevents the
# repository from creating ingest_index.db in environments where Chroma is
# used as the primary source of truth.
_LOCAL_DB_ENABLED = not _CHROMA_AVAILABLE_FOR_TRACKER


def _ensure_db():
    """
    Ensure the SQLite DB and table exist.

    Returns a sqlite3.Connection object.
    """
    if not _LOCAL_DB_ENABLED:
        # Local DB disabled when Chroma is available; return None to signal
        # callers that local tracking is inactive.
        return None

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
    # NOTE: We intentionally avoid writing to the `conversations` DB model
    # `IngestedDocument`. Per project decision, ingestion deduplication is
    # performed against Chroma metadata instead. We keep a local ingest_index.db
    # only when Chroma is not available.
    conn = _ensure_db()
    if conn is None:
        # local DB disabled; nothing to record
        return
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
    # Do not consult the conversations DB; prefer the local ingest index only.
    # If local DB is disabled prefer returning False so callers will consult
    # Chroma (or other mechanisms) instead.
    if not _LOCAL_DB_ENABLED:
        return False
    conn = _ensure_db()
    if conn is None:
        return False
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
    # Prefer local ingest index; do not read from conversations DB table.
    if not _LOCAL_DB_ENABLED:
        return None
    conn = _ensure_db()
    if conn is None:
        return None
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
    # Only update local ingest index when enabled.
    if not _LOCAL_DB_ENABLED:
        return
    conn = _ensure_db()
    if conn is None:
        return
    cur = conn.cursor()
    cur.execute("UPDATE ingested_docs SET upserted=1 WHERE content_hash=?", (content_hash,))
    conn.commit()
    try:
        conn.close()
    except Exception:
        pass


def exists_by_source(filename: str) -> bool:
    """Return True if any vector in Chroma has metadata `source` equal to filename.

    This is a best-effort scan that uses the Chroma client API. It is used to
    determine whether a file (by its original filename) was already ingested.
    """
    if not filename:
        return False
    try:
        # First try via the Chroma client API (recommended/portable).
        from app.services.vectorstore.chroma_client import ChromaClient
        client = ChromaClient(embed_model=None)
        coll = getattr(client, 'collection', None)
        if coll:
            try:
                res = coll.get(include=['metadatas'])
                metas = res.get('metadatas', [[]])[0]
            except Exception:
                try:
                    res = coll.get()
                    metas = res.get('metadatas', [[]])[0]
                except Exception:
                    metas = []
            for md in metas:
                if isinstance(md, dict):
                    # tolerate several metadata key names
                    if md.get('source') == filename or md.get('original_filename') == filename:
                        return True
    except Exception:
        # continue to sqlite fallback
        pass

    # Fallback: try to locate a chroma sqlite DB file in common locations
    # within the configured persist directory and do a generic substring
    # search across text columns. This is intentionally generic to be
    # resilient to schema differences between chromadb versions.
    try:
        # Attempt to discover persist directory by instantiating ChromaClient
        from app.services.vectorstore.chroma_client import ChromaClient
        client_probe = ChromaClient(embed_model=None)
        pd = getattr(client_probe, 'persist_directory', None)
        if not pd:
            return False
        p = Path(pd)
        # common filename for chroma sqlite DB
        candidates = [p / 'chroma.sqlite3', p / 'chroma.db', p / 'chromadb.sqlite']
        # also consider any .sqlite3 in the folder
        candidates += list(p.glob('*.sqlite3'))
        found = None
        for c in candidates:
            if c and c.exists():
                found = c
                break
        if not found:
            return False

        import sqlite3 as _sqlite
        conn = _sqlite.connect(str(found))
        cur = conn.cursor()
        # Get table names
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        for tbl in tables:
            try:
                # get columns
                cur.execute(f"PRAGMA table_info('{tbl}')")
                cols = cur.fetchall()
                text_cols = [c[1] for c in cols if c[2].upper().find('CHAR') != -1 or c[2].upper().find('TEXT') != -1]
                if not text_cols:
                    # try any column if schema unknown
                    text_cols = [c[1] for c in cols]
                for col in text_cols:
                    try:
                        q = f"SELECT 1 FROM {tbl} WHERE {col} LIKE ? LIMIT 1"
                        cur.execute(q, (f"%{filename}%",))
                        if cur.fetchone():
                            conn.close()
                            return True
                    except Exception:
                        continue
            except Exception:
                continue
        conn.close()
    except Exception:
        return False
    return False
