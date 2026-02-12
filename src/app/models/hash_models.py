"""
@file hash_models.py
@author naflashDev
@brief SQLAlchemy models for hash tables.
@details Defines tables for MD5, SHA256, and SHA512 hashes.
"""

from sqlalchemy import Column, Integer, String, DateTime
from .db import Base
from datetime import datetime

class MD5Hash(Base):
    '''
    @brief Table for MD5 hashes.
    '''
    __tablename__ = "md5_hashes"
    id = Column(Integer, primary_key=True, index=True)
    original_value = Column(String, nullable=False)
    hashed_value = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SHA256Hash(Base):
    '''
    @brief Table for SHA256 hashes.
    '''
    __tablename__ = "sha256_hashes"
    id = Column(Integer, primary_key=True, index=True)
    original_value = Column(String, nullable=False)
    hashed_value = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SHA512Hash(Base):
    '''
    @brief Table for SHA512 hashes.
    '''
    __tablename__ = "sha512_hashes"
    id = Column(Integer, primary_key=True, index=True)
    original_value = Column(String, nullable=False)
    hashed_value = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
