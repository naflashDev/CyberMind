"""
@file conversation_db.py
@brief Separate DB connection for conversation storage.
@details Uses a different SQLite file to store conversations and messages
so `hashed.db` can be reserved for hashing services.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Default DB URL for conversations
SQLALCHEMY_CONVERSATION_DB_URL = "sqlite:///./conversations.db"
ConversationBase = declarative_base()


def set_conversation_db_url(url: str = None):
    global SQLALCHEMY_CONVERSATION_DB_URL, engine, SessionLocal
    if url:
        SQLALCHEMY_CONVERSATION_DB_URL = url
    from sqlalchemy.pool import StaticPool
    if SQLALCHEMY_CONVERSATION_DB_URL == "sqlite:///:memory:":
        engine = create_engine(
            SQLALCHEMY_CONVERSATION_DB_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
    else:
        engine = create_engine(
            SQLALCHEMY_CONVERSATION_DB_URL,
            connect_args={"check_same_thread": False}
        )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Initialize with default URL
set_conversation_db_url(SQLALCHEMY_CONVERSATION_DB_URL)


def get_conv_db():
    """
    Dependency generator for conversation DB session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
