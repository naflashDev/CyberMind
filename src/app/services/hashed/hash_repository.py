"""
@file hash_repository.py
@author naflashDev
@brief Repository for hash storage and retrieval.
@details Handles database operations for hash tables by algorithm.
"""

from enum import Enum
from sqlalchemy.orm import Session
from ...models.hash_models import MD5Hash, SHA256Hash, SHA512Hash
from datetime import datetime

class HashAlgorithm(str, Enum):
    MD5 = "MD5"
    SHA256 = "SHA256"
    SHA512 = "SHA512"

class HashRepository:
    '''
    @brief Repository for hash DB operations.

    @param db_session SQLAlchemy session for DB operations.
    '''
    def __init__(self, db_session: Session):
        # Store the database session
        self.db_session = db_session

    def save_hash(self, original_value: str, hashed_value: str, algorithm: HashAlgorithm):
        '''
        @brief Save a hash and its original value in the appropriate table.

        @param original_value The original phrase.
        @param hashed_value The hash value.
        @param algorithm The hash algorithm used.
        @return None
        '''
        # Choose model by algorithm
        if algorithm == HashAlgorithm.MD5:
            obj = MD5Hash(original_value=original_value, hashed_value=hashed_value)
        elif algorithm == HashAlgorithm.SHA256:
            obj = SHA256Hash(original_value=original_value, hashed_value=hashed_value)
        elif algorithm == HashAlgorithm.SHA512:
            obj = SHA512Hash(original_value=original_value, hashed_value=hashed_value)
        else:
            raise ValueError("Unsupported algorithm")
        # Add and commit
        self.db_session.add(obj)
        self.db_session.commit()

    def get_original_by_hash(self, hashed_value: str, algorithm: HashAlgorithm):
        '''
        @brief Retrieve the original value for a given hash.

        @param hashed_value The hash value to look up.
        @param algorithm The hash algorithm used.
        @return The original value if found, else None.
        '''
        # Select model by algorithm
        if algorithm == HashAlgorithm.MD5:
            model = MD5Hash
        elif algorithm == HashAlgorithm.SHA256:
            model = SHA256Hash
        elif algorithm == HashAlgorithm.SHA512:
            model = SHA512Hash
        else:
            raise ValueError("Unsupported algorithm")
        # Query for hash
        record = self.db_session.query(model).filter_by(hashed_value=hashed_value).first()
        if record:
            return record.original_value
        return None
