"""
@file chroma_client.py
@author naflashDev
@brief Minimal Chroma vectorstore client scaffold.
@details Provides a thin wrapper over Chroma (if available) and an embedding adapter.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

import chromadb
from chromadb.config import Settings

from sentence_transformers import SentenceTransformer
import os
from pathlib import Path
import logging
import shutil
import json
from ..vectorstore.ollama_adapter import OllamaEmbeddingAdapter

# Assume chromadb and sentence-transformers are installed
CHROMA_AVAILABLE = True
EMB_MODEL_AVAILABLE = True


class EmbeddingAdapter:
    """Adapter to produce embeddings from a local model only.

    This adapter enforces "local-only" mode: it will attempt to load the model
    from a local path and will NOT attempt to contact Hugging Face or other
    remote services. If the local model cannot be found, it raises an
    informative RuntimeError so the caller can decide how to proceed.

    Usage:
      EmbeddingAdapter(model_name="all-MiniLM-L6-v2")
      EmbeddingAdapter(model_path="/opt/models/cybersentinel")
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", model_path: Optional[str] = None, offline: bool = True):
        self.model_name = model_name
        # Resolve candidate local paths (explicit path > ./models/{name} > ./models/{name.replace('/', '-')})
        candidates = []
        if model_path:
            candidates.append(Path(model_path))
        # check project-local models directory
        local_folder = Path(__file__).resolve().parents[3] / "models"
        candidates.append(local_folder / model_name)
        # also try a sanitized folder name (replace / with -)
        candidates.append(local_folder / model_name.replace('/', '-'))

        found = None
        for p in candidates:
            try:
                if p and p.exists():
                    found = p
                    break
            except Exception:
                continue

        if not found:
            raise RuntimeError(
                f"Embedding model not found locally. Expected model at one of: {', '.join([str(x) for x in candidates])}.\n"
                "Place the CyberSentinel embedding model files in the 'models' directory or pass 'model_path' pointing to the local model folder.\n"
                "This application is configured to use local models only (no network downloads)."
            )

        # Enforce offline mode to avoid accidental network calls from transformers/huggingface
        if offline:
            os.environ.setdefault('HUGGINGFACE_HUB_OFFLINE', '1')
            os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')

        try:
            # Load SentenceTransformer from local folder
            self.model = SentenceTransformer(str(found))
        except Exception as e:
            raise RuntimeError(f"Failed to load local embedding model from {found}: {e}")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, show_progress_bar=False).tolist()


class ChromaClient:
    """Thin wrapper for Chroma vector store operations.

    Methods implemented as stubs if chromadb is not installed.
    """
    def __init__(self, persist_directory: str = "data/chroma", collection_name: str = "default", embed_model: Optional[EmbeddingAdapter] = None):
        # Resolve persist directory to an absolute path so Chroma writes to disk reliably
        try:
            self.persist_directory = str(Path(persist_directory).resolve())
        except Exception:
            # fallback to raw string if resolution fails
            self.persist_directory = persist_directory
        self.collection_name = collection_name
        # Prefer explicit embed_model. Otherwise, always prefer Ollama as the default
        # embedding provider (user requested Ollama-only mode). If Ollama is not
        # available, leave embedder as None and warn.
        if embed_model is not None:
            self.embedder = embed_model
        else:
            # Do not auto-select external embedding providers by default to avoid
            # unexpected external CLI calls in environments (tests, CI, etc.).
            # Prefer explicitly passing an `embed_model` when embeddings are
            # required (e.g., during document ingest). If an environment variable
            # requests an Ollama-based embedder, the application can construct
            # the adapter and pass it explicitly.
            logging.getLogger(__name__).warning('No embed_model provided; embeddings disabled by default. Pass an EmbeddingAdapter to enable vectorization.')
            self.embedder = None
        # Silence chromadb deprecation/info logs and create client. If the
        # chromadb API raises or logs deprecation warnings, prefer to continue
        # operating without a collection rather than crash the app.
        try:
            logging.getLogger('chromadb').setLevel(logging.ERROR)
        except Exception:
            pass

        # Attempt multiple client construction patterns for compatibility
        self.client = None
        self.collection = None
        try:
            # Ensure persist directory exists so Chroma can write files
            try:
                Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

            # Preferred: construct client with explicit Settings to enable persistence
            try:
                self.client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=self.persist_directory))
            except Exception:
                # Fallback: try a simple, modern constructor without Settings
                try:
                    self.client = chromadb.Client()
                except Exception:
                    # Final fallback: some environments expose a `chroma` package
                    try:
                        import chroma as chroma_mod  # type: ignore
                        if hasattr(chroma_mod, 'ChromaClient'):
                            # prefer passing persist_directory if supported by this variant
                            try:
                                self.client = chroma_mod.ChromaClient(persist_directory=self.persist_directory)
                            except Exception:
                                self.client = chroma_mod.ChromaClient()
                    except Exception:
                        pass

            # If the client was created but doesn't expose a persist() method, try to reconstruct
            # it explicitly with Settings to force on-disk persistence.
            if self.client and not getattr(self.client, 'persist', None):
                try:
                    self.client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=self.persist_directory))
                except Exception:
                    # give up; some environments may not support persistence API
                    pass

            # If we have a client, attempt to get or create the collection
            if self.client:
                try:
                    if hasattr(self.client, 'get_collection'):
                        self.collection = self.client.get_collection(self.collection_name)
                    else:
                        # Some client variants may expose different collection APIs
                        self.collection = None
                    if not self.collection and hasattr(self.client, 'create_collection'):
                        self.collection = self.client.create_collection(self.collection_name)
                except Exception:
                    try:
                        self.collection = self.client.create_collection(self.collection_name)
                    except Exception:
                        self.collection = None
            # Track whether we can call persist() on this client
            self._can_persist = bool(getattr(self.client, 'persist', None))
        except Exception as e:
            logging.getLogger(__name__).warning('Failed to initialize Chroma client: %s', e)
            self.client = None
            self.collection = None

        # Backup file used when Chroma client does not support persist()
        try:
            self._backup_path = Path(self.persist_directory) / 'chroma_backup.jsonl'
        except Exception:
            self._backup_path = None

        # If we have a collection and a backup exists, attempt to restore from it
        try:
            if getattr(self, 'collection', None) and self._backup_path and self._backup_path.exists():
                try:
                    self._restore_from_backup()
                except Exception:
                    # do not fail startup on restore issues
                    logging.getLogger(__name__).warning('Failed to restore chroma backup; continuing')
        except Exception:
            pass

    def _persist_safe(self):
        """Try to persist the client state to disk if supported.

        This centralizes error handling around persist operations and ensures we
        attempt a best-effort persist to the resolved persist_directory.
        """
        if not getattr(self, 'client', None):
            return False
        if not getattr(self, '_can_persist', False):
            return False
        try:
            # call persist; some client implementations accept no args
            self.client.persist()
            return True
        except Exception:
            try:
                # Some variants may expose 'persist' on a different attribute
                alt = getattr(self.client, 'persist', None)
                if callable(alt):
                    alt()
                    return True
            except Exception:
                pass
        return False

    def _write_backup_entries(self, entries: List[Dict], overwrite: bool = False):
        """Write provided entries to the backup JSONL file.

        Each entry must be a dict with keys: id, embedding, metadata, document
        If overwrite is True the file is replaced; otherwise entries are appended.
        """
        if not self._backup_path:
            return False
        try:
            mode = 'w' if overwrite else 'a'
            with open(self._backup_path, mode, encoding='utf-8') as wf:
                for e in entries:
                    try:
                        wf.write(json.dumps(e, ensure_ascii=False) + '\n')
                    except Exception:
                        # skip entries that cannot be serialized
                        continue
            return True
        except Exception:
            return False

    def _restore_from_backup(self):
        """Restore vectors from the JSONL backup into the current collection.

        This is best-effort: failures do not crash the application.
        """
        if not self._backup_path or not self._backup_path.exists():
            return False
        if not getattr(self, 'collection', None):
            return False
        import json as _json
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        try:
            with open(self._backup_path, 'r', encoding='utf-8') as rf:
                for line in rf:
                    try:
                        obj = _json.loads(line)
                        ids.append(obj.get('id'))
                        embeddings.append(obj.get('embedding'))
                        metadatas.append(obj.get('metadata'))
                        documents.append(obj.get('document'))
                    except Exception:
                        continue
        except Exception:
            return False

        if not ids:
            return False

        try:
            # Use upsert if available to avoid duplicates
            if getattr(self.collection, 'upsert', None):
                try:
                    self.collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
                except Exception:
                    # fallback to add
                    self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
            else:
                self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
            # after restore attempt to persist via client if possible
            try:
                self._persist_safe()
            except Exception:
                pass
            return True
        except Exception:
            return False

    def build_collection(self, docs: List[Dict]):
        """Build or replace collection from list of docs. Each doc must have `id`, `text`, and optional `metadata`.

        This method will compute embeddings and upsert into Chroma.
        """
        # Compute embeddings and upsert into Chroma

        texts = [d["text"] for d in docs]
        ids = [str(d["id"]) for d in docs]
        metadatas = [d.get("metadata", {}) for d in docs]
        if not self.embedder:
            logging.getLogger(__name__).warning('No embedder available; skipping Chroma upsert')
            return
        if not self.collection:
            logging.getLogger(__name__).warning('Chroma collection not initialized; skipping upsert')
            return
        embeddings = self.embedder.embed_texts(texts)
        # Upsert in a single batch
        self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=texts)
        # Write a full backup file (overwrite) so vectors are available on disk even
        # if the Chroma client does not expose a persist() method
        try:
            entries = []
            for i, _id in enumerate(ids):
                entries.append({
                    'id': _id,
                    'embedding': embeddings[i],
                    'metadata': metadatas[i],
                    'document': texts[i]
                })
            try:
                self._write_backup_entries(entries, overwrite=True)
            except Exception:
                pass
        except Exception:
            pass
        # Best-effort: persist collection to disk
        try:
            self._persist_safe()
        except Exception:
            pass

    def upsert_document(self, doc_id: str, text: str, metadata: Optional[Dict] = None):
        """Upsert a single document into the collection."""
        if not self.embedder:
            logging.getLogger(__name__).warning('No embedder available; skipping single document upsert for %s', doc_id)
            return
        if not self.collection:
            logging.getLogger(__name__).warning('Chroma collection not initialized; skipping single document upsert for %s', doc_id)
            return
        # Split document into chunks and upsert each chunk as a separate vector
        try:
            CHUNK_SIZE = int(os.getenv('CHROMA_DOC_CHUNK_CHARS', '800'))
        except Exception:
            CHUNK_SIZE = 800

        def _split_into_chunks(s: str, max_chars: int):
            words = s.split()
            chunks = []
            cur = []
            cur_len = 0
            for w in words:
                wl = len(w) + 1
                if cur_len + wl > max_chars and cur:
                    chunks.append(' '.join(cur))
                    cur = [w]
                    cur_len = len(w)
                else:
                    cur.append(w)
                    cur_len += wl
            if cur:
                chunks.append(' '.join(cur))
            if not chunks and s:
                for i in range(0, len(s), max_chars):
                    chunks.append(s[i:i+max_chars])
            return chunks

        chunks = _split_into_chunks(text or '', CHUNK_SIZE)
        if not chunks:
            chunks = ['']

        embeddings = self.embedder.embed_texts(chunks)
        ids = [f"{doc_id}#{i}" for i in range(len(chunks))]
        metadatas = []
        for i, c in enumerate(chunks):
            md = dict(metadata or {})
            md.update({'doc_id': doc_id, 'chunk_index': i, 'chunk_preview': c[:200]})
            metadatas.append(md)

        try:
            # Use upsert so we overwrite previous chunk vectors for this doc id
            self.collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=chunks)
        except Exception:
            # Fallback to add if upsert is not available on this client variant
            try:
                self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=chunks)
            except Exception as e:
                logging.getLogger(__name__).warning('Failed to upsert/add chunks for %s: %s', doc_id, e)
                return

        # Append new entries to the backup file so new vectors survive restarts
        try:
            entries = []
            for i, _id in enumerate(ids):
                entries.append({
                    'id': _id,
                    'embedding': embeddings[i],
                    'metadata': metadatas[i],
                    'document': chunks[i]
                })
            try:
                self._write_backup_entries(entries, overwrite=False)
            except Exception:
                pass
        except Exception:
            pass

        # Best-effort: persist collection to disk
        try:
            self._persist_safe()
        except Exception:
            pass

    def query_retriever(self, query: str, k: int = 5) -> List[Dict]:
        """Return top-k documents for query as list of {id, text, metadata, score}.

        Uses embedding + similarity search.
        """
        if not self.embedder:
            logging.getLogger(__name__).warning('No embedder available; query_retriever returning empty')
            return []
        if not self.collection:
            logging.getLogger(__name__).warning('Chroma collection not initialized; query_retriever returning empty')
            return []
        q_emb = self.embedder.embed_texts([query])[0]
        # Note: some chroma versions do not accept 'ids' in the include list.
        # Request commonly-supported fields and derive an identifier from metadata
        results = self.collection.query(query_embeddings=[q_emb], n_results=k, include=['metadatas', 'documents', 'distances'])
        docs = []
        # results contains lists per query; we asked one query
        docs_list = results.get('documents', [[]])[0]
        metas_list = results.get('metadatas', [[]])[0]
        dists_list = results.get('distances', [[]])[0]
        for idx, doc_text in enumerate(docs_list):
            md = metas_list[idx] if idx < len(metas_list) else {}
            # Prefer explicit doc id stored in metadata (e.g., 'doc_id'), else fall back to other metadata keys
            doc_id = None
            if isinstance(md, dict):
                doc_id = md.get('doc_id') or md.get('id') or md.get('source')
            if not doc_id:
                # fallback to string index to avoid crashes
                doc_id = str(idx)
            score = dists_list[idx] if idx < len(dists_list) else None
            docs.append({
                'id': doc_id,
                'text': doc_text,
                'metadata': md,
                'score': score
            })
        return docs

    def delete_by_ttl(self, cutoff_ts: datetime):
        """Delete vectors whose metadata timestamp is older than cutoff_ts.

        Expects metadata to include an ISO `timestamp` key.
        """
        # chromadb API variants differ: some clients allowed 'ids' in include, newer
        # versions reject it. Try a safe strategy and fall back gracefully.
        try:
            try:
                res = self.collection.get(include=['ids'])
                ids_raw = res.get('ids', [])
                ids_list = ids_raw[0] if isinstance(ids_raw and ids_raw[0:1], list) else ids_raw
            except Exception:
                # Fallback: request metadatas/documents and try to extract ids from metadata
                res = self.collection.get(include=['metadatas', 'documents'])
                metas = []
                try:
                    metas = res.get('metadatas', [[]])[0]
                except Exception:
                    metas = []
                ids_list = []
                for md in metas:
                    if isinstance(md, dict):
                        # prefer explicit doc id fields if present
                        doc_id = md.get('doc_id') or md.get('id') or md.get('source')
                        if doc_id:
                            ids_list.append(doc_id)
                # If we couldn't derive ids, give up to avoid accidental mass-delete
                if not ids_list:
                    return 0

            to_delete = []
            for doc_id in ids_list:
                try:
                    rec = self.collection.get(ids=[doc_id], include=['metadatas', 'documents'])
                    md = rec.get('metadatas', [[]])[0][0] if rec.get('metadatas') else {}
                    ts = md.get('timestamp')
                    if ts:
                        try:
                            t = datetime.fromisoformat(ts)
                            if t.replace(tzinfo=timezone.utc) < cutoff_ts.replace(tzinfo=timezone.utc):
                                to_delete.append(doc_id)
                        except Exception:
                            continue
                except Exception:
                    # if per-id check fails, skip it
                    continue

            if to_delete:
                try:
                    self.collection.delete(ids=to_delete)
                except Exception:
                    # deletion may fail on some backends; swallow to keep retention robust
                    return 0
                return len(to_delete)
            return 0
        except Exception:
            return 0
