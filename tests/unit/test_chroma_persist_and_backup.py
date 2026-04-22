import json

from app.services.vectorstore.chroma_client import ChromaClient


def test_persist_safe_success(tmp_path):
    pd = tmp_path / "chroma"
    # construct client; constructor creates folders but may not initialize chroma
    cc = ChromaClient(persist_directory=str(pd), collection_name="testcol")

    class DummyClient:
        def __init__(self):
            self.called = False

        def persist(self):
            self.called = True

    cc.client = DummyClient()
    cc._can_persist = True
    # Ensure the persist callable is available as some client variants
    # expose a bound method rather than a top-level attribute. Tests should
    # simulate both possibilities so _persist_safe() exercises the direct
    # attribute-calling path.
    try:
        cc._persist_callable = cc.client.persist
    except Exception:
        cc._persist_callable = None

    assert cc._persist_safe() is True
    assert cc.client.called is True


def test_write_backup_and_restore_upsert(tmp_path):
    pd = tmp_path / "chroma"
    pd.mkdir()
    cc = ChromaClient(persist_directory=str(pd), collection_name="testcol")

    entries = [
        {
            "id": "doc1",
            "embedding": [0.1, 0.2, 0.3],
            "metadata": {"doc_id": "doc1", "timestamp": "2020-01-01T00:00:00+00:00"},
            "document": "hello world",
        }
    ]

    # Write initial backup (overwrite)
    assert cc._write_backup_entries(entries, overwrite=True) is True
    assert cc._backup_path.exists()

    # Provide a fake collection that records upsert calls
    class FakeCollection:
        def __init__(self):
            self.upsert_called = False

        def upsert(self, ids=None, embeddings=None, metadatas=None, documents=None):
            self.upsert_called = True

    cc.collection = FakeCollection()

    # restore should read the backup and call upsert on the fake collection
    assert cc._restore_from_backup() is True
    assert cc.collection.upsert_called is True
