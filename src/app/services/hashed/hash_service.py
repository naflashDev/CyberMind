from loguru import logger
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


from .bruteforce_utils import detect_hash_type, bruteforce_hash

class HashService:
    '''
    @brief Service for hashing and unhashing phrases, including brute-force and type detection.

    Handles hash generation, lookup, type detection and brute-force for supported algorithms.

    @param db_session SQLAlchemy session for DB operations.
    '''
    def __init__(self, db_session: Session):
        # Store the database session
        self.db_session = db_session
        self.repo = HashRepository(db_session)
        logger.debug("HashService initialized with DB session: {}", db_session)

    def hash_phrase(self, phrase: str, algorithm: HashAlgorithm) -> str:
        '''
        @brief Hash a phrase, show it to the user, and store it in the database only if not already present.

        Calculates the hash, checks if it exists in the DB, stores it if not, and returns the hash.

        @param phrase The phrase to hash.
        @param algorithm The hash algorithm to use.
        @return The generated hash string.
        '''
        logger.info("Hashing phrase with algorithm {}", algorithm)
        # Select hash function
        if algorithm == HashAlgorithm.MD5:
            hashed = hashlib.md5(phrase.encode()).hexdigest()
        elif algorithm == HashAlgorithm.SHA256:
            hashed = hashlib.sha256(phrase.encode()).hexdigest()
        elif algorithm == HashAlgorithm.SHA512:
            hashed = hashlib.sha512(phrase.encode()).hexdigest()
        else:
            logger.error("Unsupported algorithm: {}", algorithm)
            raise ValueError("Unsupported algorithm")

        logger.debug("Generated hash: {}", hashed)
        # Check if hash already exists in DB
        existing = self.repo.get_original_by_hash(hashed, algorithm)
        if existing is None:
            logger.info("Hash not found in DB, saving: {}", hashed)
            self.repo.save_hash(phrase, hashed, algorithm)
        else:
            logger.info("Hash already present in DB: {}", hashed)
        # Return hash to user
        return hashed

    def unhash(self, hashes: list[str], max_len: int = 20, timeout: int = 60, cpu_limit: int = 0, gpu_limit: int = 0) -> list[dict]:
        '''
        @brief Try to unhash a list of hashes, using DB and brute-force if needed.

        For each hash, detect type, search DB, and if not found, brute-force it (with timeout and count).

        @param hashes List of hash strings.
        @param max_len Maximum brute-force length.
        @return List of dicts: {hash, original, type, found, method, count, timeout}
        '''
        results = []
        logger.info("Starting unhash for {} hashes (max_len={})", len(hashes), max_len)
        for h in hashes:
            h = h.strip()
            if not h:
                logger.debug("Skipping empty hash entry")
                continue
            hash_type = detect_hash_type(h)
            if not hash_type:
                logger.warning("Unknown hash type for {}", h)
                results.append({"hash": h, "original": None, "type": None, "found": False, "method": None, "count": 0, "timeout": False})
                continue
            # Try DB
            logger.debug("Trying DB lookup for hash {} (type: {})", h, hash_type)
            original = self.repo.get_original_by_hash(h, HashAlgorithm(hash_type))
            if original is not None:
                logger.info("Hash {} found in DB", h)
                results.append({"hash": h, "original": original, "type": hash_type, "found": True, "method": "db", "count": 0, "timeout": False})
                continue
            # Brute-force (with timeout and count)
            logger.info("Hash {} not found in DB, starting brute-force", h)
            # Limitar uso de CPU/GPU si se especifica
            bf_result = bruteforce_hash(h, hash_type, max_len=max_len, timeout=timeout, cpu_limit=cpu_limit, gpu_limit=gpu_limit)
            cracked = bf_result.get('original')
            count = bf_result.get('count', 0)
            timeout_flag = bf_result.get('timeout', False)
            if cracked:
                logger.success("Brute-force successful for hash {}: {} (combinaciones: {}, timeout: {})", h, cracked, count, timeout_flag)
                # Save to DB for future queries
                self.repo.save_hash(cracked, h, HashAlgorithm(hash_type))
                results.append({"hash": h, "original": cracked, "type": hash_type, "found": True, "method": "bruteforce", "count": count, "timeout": timeout_flag})
            else:
                logger.warning("Brute-force failed for hash {} (combinaciones: {}, timeout: {})", h, count, timeout_flag)
                results.append({"hash": h, "original": None, "type": hash_type, "found": False, "method": "bruteforce", "count": count, "timeout": timeout_flag})
        logger.info("Unhash finished. {} resultados.", len(results))
        return results
