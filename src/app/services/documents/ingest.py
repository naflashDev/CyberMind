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
from io import BytesIO
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None
from app.services.documents import ingest_tracker
import re
from typing import Any

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
    # If this is a PDF, attempt to extract text using pypdf for better results.
    name = (filename or '').lower()
    if (file_bytes[:4] == b'%PDF') or name.endswith('.pdf'):
        if PdfReader is not None:
            try:
                reader = PdfReader(BytesIO(file_bytes))
                pages = []
                for p in reader.pages:
                    try:
                        txt = p.extract_text() or ''
                    except Exception:
                        txt = ''
                    pages.append(txt)
                return '\n'.join(pages)
            except Exception:
                # fallthrough to generic decoding on failure
                logger.warning('PDF text extraction via pypdf failed for %s; falling back to raw decoding', filename)
        else:
            logger.debug('pypdf not available; skipping PDF text extraction for %s', filename)

    # Very small utility: try decode utf-8, fallback latin1. For non-text files caller may extract text later.
    try:
        return file_bytes.decode('utf-8')
    except Exception:
        try:
            return file_bytes.decode('latin1')
        except Exception:
            return ''


def is_blacklisted_filename(filename: str) -> bool:
    """
    Return True for filenames that should be skipped from ingestion.

    This includes common repository metadata and delta files that are
    not useful for embeddings: delta.json, deltalog.json, README.md,
    .gitignore and .gitattributes. Comparison is case-insensitive.
    """
    if not filename:
        return False
    try:
        name = filename.lower()
        return name in ("delta.json", "deltalog.json", "readme.md", ".gitignore", ".gitattributes")
    except Exception:
        return False


def ingest_document(file_bytes: bytes, filename: str = None, folder: str = None, conversation_id: int = None, original_url: str = None, *, save_copy: bool = True, original_path: str | None = None):
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
        # Skip files that are known repository/docs metadata and should not
        # be ingested into the vectorstore (e.g., delta files, README, .gitignore)
        try:
            if is_blacklisted_filename(filename):
                logger.info('Skipping blacklisted filename=%s', filename)
                return {
                    'doc_id': None,
                    'file': filename,
                    'path': None,
                    'metadata_path': None,
                    'upserted': False,
                    'message': 'skipped_blacklisted_file',
                    'metadata': {'original_filename': filename, 'folder': str(base.as_posix())}
                }
        except Exception:
            # If blacklist check fails, continue normally
            pass
        safe_filename = (filename or 'uploaded').replace(' ', '_')
        # Compute a content-based hash to uniquely identify the document regardless
        # of the filename. This prevents re-ingesting the same bytes multiple times.
        h = sha256()
        h.update(file_bytes or b'')
        content_hash = h.hexdigest()
        # Use content_hash as canonical doc_id so vector ids are stable across uploads
        doc_id = content_hash

        logger.info('Ingest starting: filename="{}", folder="{}", size_bytes={}', safe_filename, folder, len(file_bytes or b''))
        logger.debug('Computed doc_id={}', doc_id)

        # Store only the user-friendly original filename in the target folder.
        # Avoid creating a hashed filename or metadata JSON on disk per user request.
        orig_name = safe_filename
        # First, check if a file with the same original filename was already
        # ingested into Chroma by scanning vector metadata for `source`.
        already_in_chroma = False
        try:
            already_in_chroma = ingest_tracker.exists_by_source(safe_filename)
        except Exception:
            already_in_chroma = False

        if already_in_chroma:
            logger.info(f'File {safe_filename} appears already ingested in Chroma (by source metadata)')
            return {
                'doc_id': None,
                'file': safe_filename,
                'path': None,
                'metadata_path': None,
                'upserted': True,
                'message': 'already ingested (chroma metadata)',
                'metadata': {
                    'content_hash': content_hash,
                    'original_filename': filename,
                    'folder': str(base.as_posix()),
                }
            }

        # Fallback: check local ingest tracker by content hash to avoid saving
        # duplicate bytes when filename-based check is inconclusive.
        existing = ingest_tracker.get_entry(content_hash)
        if existing:
            # Already recorded - if fully indexed, skip saving and indexing
            if existing.get('upserted'):
                logger.info('Document with content_hash=%s already ingested (stored_path=%s)', content_hash, existing.get('stored_path'))
                return {
                    'doc_id': existing.get('doc_id'),
                    'file': Path(existing.get('stored_path') or orig_name).name,
                    'path': existing.get('stored_path'),
                    'metadata_path': None,
                    'upserted': True,
                    'message': 'already ingested',
                    'metadata': {
                        'content_hash': content_hash,
                        'original_filename': filename,
                        'folder': str(base.as_posix()),
                    }
                }
            else:
                # Try to re-index into Chroma if available
                logger.info('Found previous ingest record for %s but upserted=False; attempting re-index', content_hash)
                upserted = False
                message = 'saved previously, reindex attempted'
                if _CHROMA_AVAILABLE:
                    try:
                        from app.services.vectorstore.chroma_client import ChromaClient
                        embed_model = None
                        embed_name = os.getenv('EMBED_MODEL_NAME', 'nomic-embed-text:latest')
                        try:
                            if shutil.which('ollama'):
                                embed_model = OllamaEmbeddingAdapter(model_name=embed_name)
                        except Exception:
                            embed_model = None
                        client = ChromaClient(embed_model=embed_model)
                        text = _text_from_bytes(file_bytes, filename)
                        metadata = {'preview': text[:1000], 'source': filename, 'timestamp': datetime.now(timezone.utc).isoformat()}
                        client.upsert_document(doc_id, text or metadata.get('preview', ''), metadata)
                        ingest_tracker.mark_upserted(content_hash)
                        upserted = True
                        message = 'reindexed'
                    except Exception:
                        logger.exception('Re-index attempt failed for %s', content_hash)
                return {
                    'doc_id': doc_id,
                    'file': existing.get('stored_path') and Path(existing.get('stored_path')).name or orig_name,
                    'path': existing.get('stored_path'),
                    'metadata_path': None,
                    'upserted': upserted,
                    'message': message,
                    'metadata': {'content_hash': content_hash}
                }

        stored_path = ''
        orig_path = None
        if save_copy:
            # If an original_path is provided and it already lives under the
            # data documents base, avoid creating a duplicate copy: use the
            # existing file as the stored path. This prevents the vector_ingest
            # worker from duplicating files when indexing files in-place.
            try:
                if original_path:
                    p = Path(original_path)
                    if p.exists():
                        try:
                            # check if original is inside the base documents folder
                            if str(p.resolve()).startswith(str(base.resolve())):
                                orig_path = p
                                stored_path = str(orig_path.as_posix())
                        except Exception:
                            # best-effort: fallback to path string check
                            if str(p).replace('\\', '/').lower().startswith(str(base).replace('\\', '/').lower()):
                                orig_path = p
                                stored_path = str(orig_path.as_posix())
            except Exception:
                orig_path = None

            if not orig_path:
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
                stored_path = str(orig_path.as_posix())
        else:
            # Do not create a copy on disk; use the original path when available
            try:
                stored_path = original_path or ''
                orig_path = Path(stored_path) if stored_path else None
            except Exception:
                orig_path = None
                stored_path = ''

        # minimal metadata
        md = {
            'doc_id': doc_id,
            'content_hash': content_hash,
            'original_filename': filename,
            'stored_path': stored_path,
            'folder': str(base.as_posix()),
            'conversation_id': conversation_id,
            'original_url': original_url,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        # try extract text
        text = _text_from_bytes(file_bytes, filename)

        # If this looks like a CVE JSON file (by path/filename or content),
        # build a cleaned, human-readable text to pass to the embedder at runtime
        # (do NOT overwrite or persist the original JSON).
        def _is_cve_json(filename: str | None, original_path: str | None, raw_bytes: bytes) -> bool:
            try:
                name = (filename or '').lower()
                path = (original_path or '').replace('\\', '/').lower()
                if name.endswith('.json') and ('/cves/' in path or 'cve' in path or 'cvelist' in path or name.startswith('cve-')):
                    return True
                # quick content check: JSON that contains typical CVE keys
                try:
                    j = json.loads(raw_bytes.decode('utf-8', errors='ignore'))
                except Exception:
                    return False
                if isinstance(j, dict):
                    # look for common CVE metadata locations
                    if 'cve' in j or 'CVE_data_meta' in j or any(k.lower().startswith('cve') for k in j.keys()):
                        return True
                    # files from cvelist may have 'containers' -> 'cna'
                    if 'containers' in j:
                        return True
                return False
            except Exception:
                return False

        def _collect_strings(obj: Any) -> list:
            out = []
            if isinstance(obj, str):
                out.append(obj)
            elif isinstance(obj, dict):
                for v in obj.values():
                    out.extend(_collect_strings(v))
            elif isinstance(obj, list):
                for v in obj:
                    out.extend(_collect_strings(v))
            return out

        def _cve_bytes_to_clean_text(raw_bytes: bytes) -> str:
            try:
                j = json.loads(raw_bytes.decode('utf-8', errors='ignore'))
            except Exception:
                return text

            # helpers to find nested values
            def _find_id(d: dict) -> str | None:
                # common paths for CVE id
                try:
                    if 'id' in d and isinstance(d['id'], str):
                        return d['id']
                except Exception:
                    pass
                try:
                    if 'CVE_data_meta' in d and isinstance(d['CVE_data_meta'], dict):
                        cid = d['CVE_data_meta'].get('ID') or d['CVE_data_meta'].get('id')
                        if cid:
                            return cid
                except Exception:
                    pass
                # search shallowly for strings matching CVE-YYYY-NNNN
                pattern = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)
                for v in _collect_strings(d):
                    if isinstance(v, str):
                        m = pattern.search(v)
                        if m:
                            return m.group(0).upper()
                return None

            def _extract_description(d: dict) -> str:
                # try common description locations
                candidates = []
                try:
                    # standardized cvelist containers
                    if isinstance(d.get('containers'), dict):
                        cna = d['containers'].get('cna') if isinstance(d['containers'].get('cna'), dict) else None
                        if cna:
                            desc = cna.get('summary') or cna.get('description')
                            if desc:
                                candidates.append(desc)
                            # sometimes descriptions are in 'notes' or 'problemtype'
                            if cna.get('problemtype'):
                                candidates.extend(_collect_strings(cna.get('problemtype')))
                except Exception:
                    pass
                # fallback generic search for 'description' keys
                try:
                    for s in _collect_strings(d):
                        if isinstance(s, str) and len(s) > 30:
                            candidates.append(s)
                except Exception:
                    pass

                # Deduplicate and join top candidates
                seen = []
                out = []
                for c in candidates:
                    c_clean = ' '.join(c.split())
                    if c_clean not in seen:
                        seen.append(c_clean)
                        out.append(c_clean)
                if out:
                    return '\n'.join(out[:3])
                return ''

            def _extract_refs(d: dict) -> list:
                urls = set()
                try:
                    for s in _collect_strings(d):
                        if isinstance(s, str):
                            for m in re.findall(r'https?://[^\s\]]+', s):
                                urls.add(m)
                except Exception:
                    pass
                return list(urls)

            def _extract_affects(d: dict) -> list:
                hits = []
                try:
                    # look for vendor/product strings inside configurations or affects
                    if isinstance(d.get('containers'), dict):
                        cna = d['containers'].get('cna') if isinstance(d['containers'].get('cna'), dict) else None
                        if cna and cna.get('affected'):  # newer schema
                            hits.extend(_collect_strings(cna.get('affected')))
                    # generic keys
                    for k in ('affects', 'vendors', 'products', 'configurations'):
                        if k in d:
                            hits.extend(_collect_strings(d.get(k)))
                except Exception:
                    pass
                return [ ' '.join(x.split()) for x in hits if isinstance(x, str) and len(x) > 3][:10]

            cve_id = None
            if isinstance(j, dict):
                cve_id = _find_id(j)
            if not cve_id and isinstance(j, list) and j:
                # sometimes the file is a list of records; try first element
                try:
                    if isinstance(j[0], dict):
                        cve_id = _find_id(j[0])
                except Exception:
                    pass

            desc = ''
            refs = []
            affects = []
            try:
                if isinstance(j, dict):
                    desc = _extract_description(j)
                    refs = _extract_refs(j)
                    affects = _extract_affects(j)
                elif isinstance(j, list) and j:
                    desc = _extract_description(j[0])
                    refs = _extract_refs(j[0])
                    affects = _extract_affects(j[0])
            except Exception:
                pass

            parts = []
            if cve_id:
                parts.append(f"CVE ID: {cve_id}")
            if desc:
                parts.append(f"Summary: {desc}")
            if affects:
                parts.append(f"Affected: {', '.join(affects[:10])}")
            if refs:
                parts.append(f"References: {', '.join(refs[:8])}")

            cleaned = '\n\n'.join(parts)
            # final fallback: if cleaned is empty, use flattened long strings but strip JSON keys
            if not cleaned:
                all_strings = _collect_strings(j)
                long_texts = [s for s in all_strings if isinstance(s, str) and len(s) > 50]
                cleaned = '\n\n'.join(long_texts[:3])
            # Ensure we return a sensible string
            return cleaned or text

        try:
            if _is_cve_json(filename, original_path, file_bytes):
                cleaned_text = _cve_bytes_to_clean_text(file_bytes)
                if cleaned_text and len(cleaned_text) > 0:
                    text = cleaned_text
        except Exception:
            # on any error, fall back to raw extracted text
            pass
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
                    metadata['source'] = Path(orig_path).name if orig_path is not None else metadata.get('original_filename') or metadata.get('stored_path')
                except Exception:
                    metadata['source'] = metadata.get('original_filename') or metadata.get('stored_path')
                logger.info('Attempting to upsert document {} into Chroma (embed_model={})', doc_id, embed_name if embed_model else 'None')
                try:
                    client.upsert_document(doc_id, text or metadata.get('preview', ''), metadata)
                    # Only mark as upserted if we had an embedder and a Chroma collection available.
                    try:
                        display_name = metadata.get('original_filename') or safe_filename or doc_id
                    except Exception:
                        display_name = doc_id
                    logger.success(f'Document {display_name} upsert requested')
                    if client.embedder is None:
                        logger.warning('No embedder configured; document %s was not vectorized', doc_id)
                        upserted = False
                        message = 'saved (no embedder)'
                    elif client.collection is None:
                        logger.warning('Chroma collection not initialized; document %s may not have been indexed', doc_id)
                        upserted = False
                        message = 'saved (no collection)'
                    else:
                        upserted = True
                        message = 'saved and indexed'
                except Exception as e:
                    logger.exception('Chroma upsert failed for %s: %s', doc_id, e)
                    # preserve message for caller
                    raise
            except Exception as e:
                # If chromadb import succeeded but runtime indexing failed, log succinct warning
                logger.warning('Chroma upsert failed: {}', e)
        else:
            logger.debug('Chromadb not installed; skipping vectorstore indexing for this upload')

        # Record ingestion in tracker to avoid duplicates later
        try:
            ingest_tracker.record_ingest(content_hash, doc_id, stored_path, filename, folder, upserted=bool(upserted))
        except Exception:
            logger.exception('Failed to record ingest in tracker for %s', doc_id)

        return {
            'doc_id': doc_id,
            'file': str(orig_path.name) if orig_path is not None else orig_name,
            'path': stored_path,
            'metadata_path': None,
            'upserted': upserted,
            'message': message,
            'metadata': md
        }
    except Exception as e:
        logger.exception('Error in ingest_document')
        raise
