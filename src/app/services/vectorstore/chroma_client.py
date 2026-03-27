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
        # Prefer explicit embed_model, otherwise instantiate a local-only EmbeddingAdapter
        if embed_model is not None:
            self.embedder = embed_model
        else:
            model_path_env = os.getenv('CYBERSENTINEL_MODEL_PATH')
            # default local model name expected in ./models/cybersentinel
            try:
                self.embedder = EmbeddingAdapter(model_name='cybersentinel', model_path=model_path_env)
            except Exception as e:
                # Raise early so callers know the local model is missing
                raise
        self.client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=self.persist_directory))
        # create or get collection
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            self.collection = self.client.create_collection(self.collection_name)

    def build_collection(self, docs: List[Dict]):
        """Build or replace collection from list of docs. Each doc must have `id`, `text`, and optional `metadata`.

        This method will compute embeddings and upsert into Chroma.
        """
        # Compute embeddings and upsert into Chroma

        texts = [d["text"] for d in docs]
        ids = [str(d["id"]) for d in docs]
        metadatas = [d.get("metadata", {}) for d in docs]
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
        emb = self.embedder.embed_texts([text])[0]
        self.collection.upsert(ids=[str(doc_id)], embeddings=[emb], metadatas=[metadata or {}], documents=[text])

    def query_retriever(self, query: str, k: int = 5) -> List[Dict]:
        """Return top-k documents for query as list of {id, text, metadata, score}.

        Uses embedding + similarity search.
        """
        q_emb = self.embedder.embed_texts([query])[0]
        results = self.collection.query(query_embeddings=[q_emb], n_results=k, include=['metadatas', 'documents', 'distances', 'ids'])
        docs = []
        # results contains lists per query; we asked one query
        for idx, doc_text in enumerate(results.get("documents", [[]])[0]):
            docs.append({
                "id": results.get("ids", [[]])[0][idx],
                "text": doc_text,
                "metadata": results.get("metadatas", [[]])[0][idx],
                "score": results.get("distances", [[]])[0][idx]
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
