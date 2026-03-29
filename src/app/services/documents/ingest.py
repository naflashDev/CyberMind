"""
@file ingest.py
@author naflashDev
@brief Servicio de ingestión de documentos para LLM
@details Normaliza texto de archivos subidos, guarda en disco y realiza upsert al vectorstore (Chroma).
"""
from hashlib import sha256
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import tempfile
import traceback
from loguru import logger
import shutil
from app.services.vectorstore.ollama_adapter import OllamaEmbeddingAdapter

DEFAULT_BASE = Path('data') / 'documents'

# Detect chromadb availability once to avoid noisy tracebacks on every upload
try:
    import chromadb  # type: ignore
    _CHROMA_AVAILABLE = True
except Exception:
    _CHROMA_AVAILABLE = False


def _ensure_folder(folder: str = None):
    base = DEFAULT_BASE
    if folder:
        # sanitize simple folder name
        safe = ''.join([c for c in folder if c.isalnum() or c in ('-', '_')]).strip() or 'default'
        base = base / safe
    base.mkdir(parents=True, exist_ok=True)
    return base


def _text_from_bytes(file_bytes: bytes, filename: str = None) -> str:
    # Very small utility: try decode utf-8, fallback latin1. For non-text files caller may extract text later.
    try:
        return file_bytes.decode('utf-8')
    except Exception:
        try:
            return file_bytes.decode('latin1')
        except Exception:
            return ''


def ingest_document(file_bytes: bytes, filename: str = None, folder: str = None, conversation_id: int = None, original_url: str = None):
    """
    Ingest a single uploaded file.

    Steps:
    - compute doc_id = sha256(content + filename)
    - store file under data/documents/{folder}/{doc_id}_{filename}
    - extract plain text (simple decode for text files)
    - persist metadata JSON next to file
    - attempt to upsert into Chroma (if available)

    Returns dict with doc_id, path, metadata, upserted (bool) and message.
    """
    try:
        base = _ensure_folder(folder)
        safe_filename = (filename or 'uploaded').replace(' ', '_')
        h = sha256()
        h.update(file_bytes or b'')
        h.update((safe_filename or '').encode('utf-8'))
        doc_id = h.hexdigest()

        logger.info('Ingest starting: filename="{}", folder="{}", size_bytes={}', safe_filename, folder, len(file_bytes or b''))
        logger.debug('Computed doc_id={}', doc_id)

        # Store only the user-friendly original filename in the target folder.
        # Avoid creating a hashed filename or metadata JSON on disk per user request.
        orig_name = safe_filename
        orig_path = base / orig_name
        if orig_path.exists():
            stem = Path(safe_filename).stem
            suffix = Path(safe_filename).suffix
            i = 1
            while (base / f"{stem}_{i}{suffix}").exists():
                i += 1
            orig_path = base / f"{stem}_{i}{suffix}"
        with open(orig_path, 'wb') as of:
            of.write(file_bytes)

        logger.info('Saved uploaded file to {} ({} bytes)', str(orig_path.as_posix()), orig_path.stat().st_size)

        # minimal metadata
        md = {
            'doc_id': doc_id,
            'original_filename': filename,
            'stored_path': str(orig_path.as_posix()),
            'folder': str(base.as_posix()),
            'conversation_id': conversation_id,
            'original_url': original_url,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        # try extract text
        text = _text_from_bytes(file_bytes, filename)
        logger.debug('Extracted text length: {}', len(text or ''))

        upserted = False
        message = 'saved'
        # Try to upsert into Chroma if chromadb is available and configured
        if _CHROMA_AVAILABLE:
            try:
                from app.services.vectorstore.chroma_client import ChromaClient
                # Prefer using the Nomic embedding model for generating embeddings
                embed_model = None
                embed_name = os.getenv('EMBED_MODEL_NAME', 'nomic-embed-text:latest')
                try:
                    if shutil.which('ollama'):
                        logger.info('Initializing OllamaEmbeddingAdapter with model {}', embed_name)
                        embed_model = OllamaEmbeddingAdapter(model_name=embed_name)
                except Exception as e:
                    logger.warning('Failed to initialize Ollama embedding adapter: {}', e)

                client = ChromaClient(embed_model=embed_model)
                metadata = dict(md)
                # include a short preview
                metadata['preview'] = text[:1000]
                # Include a canonical source filename for vectors so retrievers can show origin
                try:
                    metadata['source'] = Path(orig_path).name
                except Exception:
                    metadata['source'] = metadata.get('original_filename') or metadata.get('stored_path')
                logger.info('Attempting to upsert document {} into Chroma (embed_model={})', doc_id, embed_name if embed_model else 'None')
                try:
                    client.upsert_document(doc_id, text or metadata.get('preview', ''), metadata)
                    logger.success('Document {} upsert requested', doc_id)
                    upserted = True
                    message = 'saved and indexed'
                except Exception as e:
                    logger.exception('Chroma upsert failed for {}: {}', doc_id, e)
                    # preserve message for caller
                    raise
            except Exception as e:
                # If chromadb import succeeded but runtime indexing failed, log succinct warning
                logger.warning('Chroma upsert failed: {}', e)
        else:
            logger.debug('Chromadb not installed; skipping vectorstore indexing for this upload')

        return {
            'doc_id': doc_id,
            'file': str(orig_path.name),
            'path': str(orig_path.as_posix()),
            'metadata_path': None,
            'upserted': upserted,
            'message': message,
            'metadata': md
        }
    except Exception as e:
        logger.exception('Error in ingest_document')
        raise
