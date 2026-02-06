"""
@file hash_service.py
@author naflashDev
@brief Service layer for hashing and unhashing operations.
@details Provides logic for hashing phrases and retrieving original values from hashes using different algorithms.
"""

from datetime import datetime
from typing import Optional
from ...models.hash_models import MD5Hash, SHA256Hash, SHA512Hash
from ...models.db import get_db
from .hash_repository import HashRepository, HashAlgorithm

import hashlib
from sqlalchemy.orm import Session

class HashService:
    '''
    @brief Service for hashing and unhashing phrases.

    Handles hash generation and lookup for supported algorithms.

    @param db_session SQLAlchemy session for DB operations.
    '''
    def __init__(self, db_session: Session):
        # Store the database session
        self.db_session = db_session
        self.repo = HashRepository(db_session)

    def hash_phrase(self, phrase: str, algorithm: HashAlgorithm) -> str:
        '''
        @brief Hash a phrase, show it to the user, and store it in the database only if not already present.

        Calculates the hash, checks if it exists in the DB, stores it if not, and returns the hash.

        @param phrase The phrase to hash.
        @param algorithm The hash algorithm to use.
        @return The generated hash string.
        '''
        # Select hash function
        if algorithm == HashAlgorithm.MD5:
            hashed = hashlib.md5(phrase.encode()).hexdigest()
        elif algorithm == HashAlgorithm.SHA256:
            hashed = hashlib.sha256(phrase.encode()).hexdigest()
        elif algorithm == HashAlgorithm.SHA512:
            hashed = hashlib.sha512(phrase.encode()).hexdigest()
        else:
            raise ValueError("Unsupported algorithm")

        # Check if hash already exists in DB
        existing = self.repo.get_original_by_hash(hashed, algorithm)
        if existing is None:
            # Store in DB only if not present
            self.repo.save_hash(phrase, hashed, algorithm)
        # Return hash to user
        return hashed

    def unhash(self, hashed_value: str, algorithm: HashAlgorithm) -> Optional[str]:
        '''
        @brief Retrieve the original phrase for a given hash.

        @param hashed_value The hash to look up.
        @param algorithm The hash algorithm used.
        @return The original phrase if found, else None.
        '''
        # Query repository for original value
        return self.repo.get_original_by_hash(hashed_value, algorithm)
