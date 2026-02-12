"""
@file test_bruteforce_utils_resource.py
@author naflashDev
@brief Unit tests for resource limits in bruteforce_utils.
@details Cubre limitación de CPU y timeout en bruteforce_hash.
"""
import pytest
from src.app.services.hashed.bruteforce_utils import bruteforce_hash

def test_bruteforce_hash_cpu_limit():
    '''
    @brief Resource Limit: Limita el uso de CPU a 1 core (simulado, no debe fallar)
    '''
    import hashlib
    s = 'a'  # 'a' está garantizado en ALL_CHARS
    h = hashlib.md5(s.encode()).hexdigest()
    # Limita a 1 core, debe funcionar igual
    result = bruteforce_hash(h, 'MD5', max_len=1, cpu_limit=1)
    assert result['original'] == s
    assert result['timeout'] is False

def test_bruteforce_hash_timeout_short():
    '''
    @brief Timeout: Fuerza timeout bajo, debe devolver timeout True
    '''
    import hashlib
    s = 'D'
    h = hashlib.md5(s.encode()).hexdigest()
    result = bruteforce_hash(h, 'MD5', max_len=3, timeout=0.0001)
    assert result['timeout'] is True
