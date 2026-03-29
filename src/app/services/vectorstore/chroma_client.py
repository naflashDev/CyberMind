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
            # Preferred: try a simple, modern constructor first
            try:
                self.client = chromadb.Client()
            except Exception:
                # Fallback: older API that accepted a Settings object
                try:
                    self.client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=self.persist_directory))
                except Exception:
                    # Final fallback: some environments expose a `chroma` package
                    try:
                        import chroma as chroma_mod  # type: ignore
                        if hasattr(chroma_mod, 'ChromaClient'):
                            self.client = chroma_mod.ChromaClient(persist_directory=self.persist_directory)
                    except Exception:
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
        except Exception as e:
            logging.getLogger(__name__).warning('Failed to initialize Chroma client: %s', e)
            self.client = None
            self.collection = None

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
        if hasattr(self.client, "persist"):
            try:
                self.client.persist()
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
        emb = self.embedder.embed_texts([text])[0]
        self.collection.upsert(ids=[str(doc_id)], embeddings=[emb], metadatas=[metadata or {}], documents=[text])
        # Persist client state when possible so embeddings survive restarts
        if hasattr(self.client, "persist"):
            try:
                self.client.persist()
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
        # chromadb does not support server-side predicates in a uniform way; iterate and delete
        all_ids = self.collection.get(include=['ids']).get('ids', [])
        if not all_ids:
            return 0
        to_delete = []
        # flatten ids list
        ids_list = all_ids[0] if isinstance(all_ids[0], list) else all_ids
        for doc_id in ids_list:
            rec = self.collection.get(ids=[doc_id], include=['metadatas', 'documents', 'ids'])
            md = rec.get('metadatas', [[]])[0][0] if rec.get('metadatas') else {}
            ts = md.get('timestamp')
            if ts:
                try:
                    t = datetime.fromisoformat(ts)
                    if t.replace(tzinfo=timezone.utc) < cutoff_ts.replace(tzinfo=timezone.utc):
                        to_delete.append(doc_id)
                except Exception:
                    continue
        if to_delete:
            self.collection.delete(ids=to_delete)
            return len(to_delete)
        return 0
