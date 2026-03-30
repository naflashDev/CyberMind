"""
@file ingested_document.py
@brief SQLAlchemy model to record ingested documents in the conversations DB.
@details This model is intended to be created in the same SQLite used for
conversations (ConversationBase) so the app has a single DB file for runtime
data. The table stores content_hash, doc_id, paths, filename, folder, timestamp
and upserted flag.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from .conversation_db import ConversationBase as Base


class IngestedDocument(Base):
    __tablename__ = 'ingested_documents'
    # Use content_hash as primary key to avoid duplicates
    content_hash = Column(String(64), primary_key=True, index=True)
    doc_id = Column(String(128), nullable=False)
    stored_path = Column(String(1024), nullable=True)
    filename = Column(String(512), nullable=True)
    folder = Column(String(256), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    upserted = Column(Boolean, default=False)
