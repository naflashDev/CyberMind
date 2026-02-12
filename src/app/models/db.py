"""
@file db.py
@author naflashDev
@brief Database connection and session management.
@details Configures SQLite engine and session for SQLAlchemy ORM.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Permite cambiar la URL, engine y sesión dinámicamente para tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./hashed.db"
Base = declarative_base()

def set_db_url(url):
    global SQLALCHEMY_DATABASE_URL, engine, SessionLocal
    SQLALCHEMY_DATABASE_URL = url
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Inicializa por defecto
set_db_url(SQLALCHEMY_DATABASE_URL)

def get_db():
    '''
    @brief Dependency to get DB session.
    @return SQLAlchemy session generator.
    '''
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
