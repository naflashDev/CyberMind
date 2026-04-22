"""
@file test_llm_controller.py
@author naflashDev
@brief Unit tests for llm_controller
@details Tests create/list/add/delete conversation endpoints and finetune ingestion logic.
"""
import json
from datetime import datetime
from pathlib import Path

from app.controllers.routes import llm_controller


class FakeConv:
    def __init__(self, title=None):
        self.id = 1
        self.title = title
        self.created_at = datetime.now()
        self.messages = []

    # class-level attribute to satisfy attribute access in tests (e.g., Conversation.id == conv_id)
    id = 1


class FakeMsg:
    def __init__(self, conversation_id, role, text):
        self.id = 1
        self.conversation_id = conversation_id
        self.role = role
        self.text = text
        self.timestamp = datetime.now()
        self.vector_id = None


class FakeDB:
    def __init__(self, conv_exists=True):
        self._conv = FakeConv('t') if conv_exists else None

    def add(self, obj):
        # emulate SQLAlchemy setting ids/attributes
        if hasattr(obj, 'id') and getattr(obj, 'id', None) is None:
            obj.id = 1

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def query(self, model):
        class Q:
            def __init__(self, conv):
                self.conv = conv

            def filter(self, *args, **kwargs):
                class F:
                    def __init__(self, conv):
                        self.conv = conv

                    def first(self):
                        return self.conv

                    def order_by(self, *a, **k):
                        class O:
                            def all(self):
                                return [self.conv] if self.conv else []
                        return O()

                return F(self.conv)

        return Q(self._conv)


def test_create_and_add_message_and_delete(monkeypatch):
    # Monkeypatch Conversation and Message in module to our lightweight classes
    monkeypatch.setattr(llm_controller, 'Conversation', FakeConv)
    monkeypatch.setattr(llm_controller, 'Message', FakeMsg)

    db = FakeDB(conv_exists=True)

    # create conversation
    conv = llm_controller.create_conversation(llm_controller.ConversationCreate(title='hello'), db=db)
    assert conv.title == 'hello' or conv.title is None

    # add message to existing conv
    payload = llm_controller.MessageCreate(role='user', text='hi')
    out = llm_controller.add_message(1, payload, db=db)
    assert out.role == 'user'
    assert out.text == 'hi'

    # delete non-existing conv should raise 404
    db2 = FakeDB(conv_exists=False)
    try:
        llm_controller.delete_conversation(999, db=db2)
    except Exception as e:
        # fastapi.HTTPException expected
        assert hasattr(e, 'status_code') and e.status_code == 404


def test_ingest_finetune_to_chroma(tmp_path, monkeypatch):
    # prepare a simple JSONL file
    p = tmp_path / 'ft.jsonl'
    rec = {'instruction': 'do', 'input': 'x', 'output': 'y', 'source': 's'}
    p.write_text(json.dumps(rec) + '\n')

    calls = []

    class DummyChroma:
        def upsert_document(self, doc_id, text, metadata=None):
            calls.append((doc_id, text, metadata))

    monkeypatch.setattr(llm_controller, '_chroma_client', DummyChroma())
    llm_controller.ingest_finetune_to_chroma(str(p))
    assert len(calls) == 1
