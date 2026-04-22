"""
@file retention_worker.py
@brief Background worker to purge old vectors and conversation messages.
@details Runs periodically and deletes Chroma vectors and DB messages/conversations older than a TTL (default 7 days).
"""
import threading
import time
from datetime import datetime, timedelta, timezone
from loguru import logger

try:
    from app.services.vectorstore.chroma_client import ChromaClient
    CHROMA_AVAILABLE = True
except Exception:
    ChromaClient = None
    CHROMA_AVAILABLE = False

from app.models.db import SessionLocal
from app.models.conversation_db import SessionLocal as ConversationSessionLocal
from app.models.conversation import Message, Conversation
from sqlalchemy.exc import OperationalError


def vector_and_message_retention(stop_event: threading.Event, days: int = 7, interval_hours: int = 24):
    """Run retention loop until stop_event is set.

    - Deletes Chroma vectors older than `days`.
    - Deletes `Message` rows older than `days` and `Conversation` rows older than `days`.
    """
    logger.info(f"[Retention] Starting retention worker: purge items older than {days} days every {interval_hours}h")
    chroma = None
    if CHROMA_AVAILABLE:
        try:
            # Provide an embed_model when possible so retention operations can interact with vectors
            embed_model = None
            try:
                from app.services.vectorstore.ollama_adapter import OllamaEmbeddingAdapter
                import shutil, os
                if shutil.which('ollama'):
                    embed_name = os.getenv('EMBED_MODEL_NAME', 'nomic-embed-text:latest')
                    try:
                        embed_model = OllamaEmbeddingAdapter(model_name=embed_name)
                    except Exception:
                        embed_model = None
            except Exception:
                embed_model = None
            chroma = ChromaClient(embed_model=embed_model)
        except Exception:
            logger.exception("[Retention] Failed to initialize ChromaClient; will skip vector purging.")

    interval = max(1, interval_hours) * 60 * 60

    while not stop_event.is_set():
        try:
            cutoff = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=days)
            # Chroma purge
            if chroma is not None:
                try:
                    deleted = chroma.delete_by_ttl(cutoff)
                    logger.info(f"[Retention] Deleted {deleted} vectors older than {cutoff.isoformat()}")
                except Exception:
                    logger.exception("[Retention] Error deleting vectors from Chroma")

            # DB purge
            try:
                db = SessionLocal()
                try:
                    # Use the conversation-specific DB (conversations.db) for Message/Conversation tables
                    db.close()
                    db = ConversationSessionLocal()
                    # delete old messages (if table exists)
                    msg_q = db.query(Message).filter(Message.timestamp < cutoff.replace(tzinfo=None))
                    deleted_msgs = msg_q.delete(synchronize_session=False)
                    db.commit()
                    # delete conversations older than cutoff
                    conv_q = db.query(Conversation).filter(Conversation.created_at < cutoff.replace(tzinfo=None))
                    deleted_convs = conv_q.delete(synchronize_session=False)
                    db.commit()
                    logger.info(f"[Retention] Deleted {deleted_msgs} messages and {deleted_convs} conversations older than {cutoff.isoformat()}")
                except OperationalError as oe:
                    # Likely the DB/tables are not initialized in this environment; log concise warning and continue
                    logger.warning(f"[Retention] Skipping DB purge (OperationalError): {oe}")
                except Exception:
                    logger.exception("[Retention] Error purging DB messages/conversations")
                finally:
                    try:
                        db.close()
                    except Exception:
                        pass
            except Exception:
                logger.exception("[Retention] Failed acquiring DB session for purge")

        except Exception:
            logger.exception("[Retention] Unexpected error in retention loop")

        # wait with interruptible sleep
        try:
            stop_event.wait(interval)
        except Exception:
            time.sleep(5)

    logger.info("[Retention] Stopping retention worker")
