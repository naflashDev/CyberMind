"""
@file test_multi_unhash.py
@author naflashDev
@brief Unit tests for multi_unhash endpoint and service logic.
@details Covers happy path, edge and error cases for multi-unhash (DB and brute-force).
"""
import pytest
from unittest.mock import MagicMock
from src.app.services.hashed.hash_service import HashService

class DummyRepo:
    def __init__(self, found_map):
        self.found_map = found_map
        self.saved = []
    def get_original_by_hash(self, h, alg):
        # Ignore algorithm for test, just return by hash
        return self.found_map.get(h)
    def save_hash(self, original_value, hashed_value, algorithm):
        # Simulate saving to DB (for test, just record call)
        self.saved.append((original_value, hashed_value, algorithm))

def test_multi_unhash_db_and_bruteforce(monkeypatch):
    '''
    @brief Happy Path: unhash returns DB result if found, else brute-force
    '''
    db_hash = 'd41d8cd98f00b204e9800998ecf8427e'  # MD5 of ''
    bf_hash = '7fc56270e7a70fa81a5935b72eacbe29'  # MD5 of 'A'
    found_map = {db_hash: ''}
    service = HashService(None)
    service.repo = DummyRepo(found_map)
    # Patch bruteforce_hash to return dict simulating found
    def fake_bruteforce_hash(*args, **kwargs):
        h = args[0] if args else kwargs.get('hash_str')
        if h == bf_hash:
            return {'original': 'A', 'count': 123, 'timeout': False}
        return {'original': None, 'count': 123, 'timeout': True}
    monkeypatch.setattr('src.app.services.hashed.hash_service.bruteforce_hash', fake_bruteforce_hash)
    results = service.unhash([db_hash, bf_hash], max_len=1)
    # DB result
    assert results[0]['hash'] == db_hash
    assert results[0]['found'] is True
    assert results[0]['method'] == 'db'
    assert results[0]['original'] == ''
    assert results[0]['count'] == 0
    assert results[0]['timeout'] is False
    # Brute-force result
    assert results[1]['hash'] == bf_hash
    assert results[1]['found'] is True
    assert results[1]['method'] == 'bruteforce'
    assert results[1]['original'] == 'A'
    assert results[1]['count'] == 123
    assert results[1]['timeout'] is False

def test_multi_unhash_type_detection():
    '''
    @brief Edge Case: Unknown hash type returns not found
    '''
    service = HashService(None)
    service.repo = DummyRepo({})
    results = service.unhash(['notahash'], max_len=1)
    assert not results[0]['found']
    assert results[0]['type'] is None

def test_multi_unhash_empty_lines():
    '''
    @brief Edge Case: Ignores empty lines
    '''
    service = HashService(None)
    service.repo = DummyRepo({})
    results = service.unhash(['', '   ', '\n'], max_len=1)
    assert results == []
