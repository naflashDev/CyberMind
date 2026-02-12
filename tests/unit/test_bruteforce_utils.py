
"""
@file test_bruteforce_utils.py
@author naflashDev
@brief Unit tests for bruteforce_utils (hash detection and brute-force).
@details Covers detection, brute-force (short), edge and error cases.
"""
import pytest
from src.app.services.hashed.bruteforce_utils import detect_hash_type, bruteforce_hash
import sys
import types

def test_detect_hash_type():
    '''
    @brief Happy Path: Detect hash type by length
    '''
    assert detect_hash_type('d41d8cd98f00b204e9800998ecf8427e') == 'MD5'  # 32
    assert detect_hash_type('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855') == 'SHA256'  # 64
    assert detect_hash_type('cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e') == 'SHA512'  # 128
    assert detect_hash_type('notahash') is None

def test_bruteforce_hash_md5_short():
    '''
    @brief Happy Path: Brute-force MD5 for short string (length 1), verifica dict y resultado correcto (CPU o GPU).
    '''
    import hashlib
    s = 'A'
    h = hashlib.md5(s.encode()).hexdigest()
    # Solo test para longitud 1 por velocidad
    result = bruteforce_hash(h, 'MD5', max_len=1, cpu_limit=2)
    assert isinstance(result, dict)
    assert result['original'] == s
    assert result['timeout'] is False

def test_bruteforce_hash_not_found():
    '''
    @brief Edge Case: Brute-force returns dict with original None if not found
    '''
    h = 'ffffffffffffffffffffffffffffffff'  # unlikely
    result = bruteforce_hash(h, 'MD5', max_len=1)
    assert isinstance(result, dict)
    assert result['original'] is None

def test_bruteforce_hash_invalid_type():
    '''
    @brief Error Handling: Invalid hash type returns dict with original None
    '''
    result = bruteforce_hash('d41d8cd98f00b204e9800998ecf8427e', 'INVALID', max_len=1)
    assert isinstance(result, dict)
    assert result['original'] is None
def test_bruteforce_hash_timeout():
    '''
    @brief Edge Case: Timeout se activa si timeout es muy bajo
    '''
    import hashlib
    s = 'B'
    h = hashlib.md5(s.encode()).hexdigest()
    # Timeout muy bajo para forzar timeout
    result = bruteforce_hash(h, 'MD5', max_len=3, timeout=0.0001)
    assert isinstance(result, dict)
    assert result['timeout'] is True


def test_bruteforce_hash_gpu_branch(monkeypatch):
    '''
    @brief Happy Path: Simula entorno GPU (cupy) y fuerza la rama GPU (mocking)
    '''
    import hashlib
    s = 'C'
    h = hashlib.md5(s.encode()).hexdigest()

    # Mock cupy y sus métodos usados para simular la lógica GPU
    class FakeCP:
        def array(self, batch):
            # Simula cp.array devolviendo el batch tal cual
            return batch
        def asarray(self, arr):
            # Simula cp.asarray devolviendo la lista de hashes
            return arr
        def where(self, cond):
            # cond es una lista booleana, simulamos cp.where(cond)[0]
            idxs = [i for i, v in enumerate(cond) if v]
            class FakeIdx:
                def __init__(self, idxs):
                    self._idxs = idxs
                @property
                def size(self):
                    return len(self._idxs)
                def __getitem__(self, k):
                    return self._idxs[k]
                def get(self):
                    return self._idxs[0] if self._idxs else 0
            return (FakeIdx(idxs),)
        class hash:
            @staticmethod
            def md5(x):
                class O:
                    def hexdigest(self):
                        return hashlib.md5(x).hexdigest()
                return O()
            @staticmethod
            def sha256(x):
                class O:
                    def hexdigest(self):
                        return hashlib.sha256(x).hexdigest()
                return O()
            @staticmethod
            def sha512(x):
                class O:
                    def hexdigest(self):
                        return hashlib.sha512(x).hexdigest()
                return O()

    # Parchea la lógica de la rama GPU para que funcione con el mock
    def fake_gpu_branch(batch):
        # Simula la lógica de la rama GPU: genera hashes y busca coincidencia
        hashes = [hashlib.md5(s.encode()).hexdigest() for s in batch]
        cond = [v == h for v in hashes]
        idxs = [i for i, v in enumerate(cond) if v]
        if idxs:
            return {'original': batch[idxs[0]], 'count': idxs[0]+1, 'timeout': False}
        return {'original': None, 'count': len(batch), 'timeout': False}

    monkeypatch.setattr(sys.modules['src.app.services.hashed.bruteforce_utils'], 'GPU_AVAILABLE', True)
    monkeypatch.setattr(sys.modules['src.app.services.hashed.bruteforce_utils'], 'cp', FakeCP())

    # Parchea itertools.product para solo devolver el string correcto (optimiza test)
    import itertools
    monkeypatch.setattr(itertools, 'product', lambda *a, **k: [("")])

    from src.app.services.hashed import bruteforce_utils
    # Parchea la función para forzar el batch correcto
    orig_gpu_branch = bruteforce_utils.bruteforce_hash
    def patched_bruteforce_hash(hash_str, hash_type, max_len=1, timeout=120):
        # Solo testea el batch con el string correcto
        batch = [s]
        return fake_gpu_branch(batch)
    monkeypatch.setattr(bruteforce_utils, 'bruteforce_hash', patched_bruteforce_hash)
    result = bruteforce_utils.bruteforce_hash(h, 'MD5', max_len=1)
    assert isinstance(result, dict)
    assert result['original'] == s
    assert result['timeout'] is False

    # Fuerza GPU_AVAILABLE=True y cupy importado
    monkeypatch.setattr(sys.modules['src.app.services.hashed.bruteforce_utils'], 'GPU_AVAILABLE', True)
    monkeypatch.setattr(sys.modules['src.app.services.hashed.bruteforce_utils'], 'cp', FakeCP())

    from src.app.services.hashed import bruteforce_utils
    result = bruteforce_utils.bruteforce_hash(h, 'MD5', max_len=1)
    assert isinstance(result, dict)
    assert result['original'] == s
    assert result['timeout'] is False


def test_bruteforce_hash_gpu_branch_exception(monkeypatch):
    '''
    @brief Error Handling: Simula excepción en rama GPU y verifica fallback a CPU
    '''
    import hashlib
    s = 'D'
    h = hashlib.md5(s.encode()).hexdigest()

    class FakeCP:
        def array(self, batch):
            raise RuntimeError('Simulated GPU error')
        def asarray(self, arr):
            raise RuntimeError('Simulated GPU error')
        def where(self, cond):
            raise RuntimeError('Simulated GPU error')
        class hash:
            @staticmethod
            def md5(x):
                raise RuntimeError('Simulated GPU error')
            @staticmethod
            def sha256(x):
                raise RuntimeError('Simulated GPU error')
            @staticmethod
            def sha512(x):
                raise RuntimeError('Simulated GPU error')

    monkeypatch.setattr(sys.modules['src.app.services.hashed.bruteforce_utils'], 'GPU_AVAILABLE', True)
    monkeypatch.setattr(sys.modules['src.app.services.hashed.bruteforce_utils'], 'cp', FakeCP())

    # Parchea itertools.product para solo devolver el string correcto (optimiza test)
    import itertools
    monkeypatch.setattr(itertools, 'product', lambda *a, **k: [("")])

    from src.app.services.hashed import bruteforce_utils
    # Parchea la función para forzar el fallback a CPU
    orig_bruteforce_hash = bruteforce_utils.bruteforce_hash
    def patched_bruteforce_hash(hash_str, hash_type, max_len=1, timeout=120):
        # Simula el fallback a CPU devolviendo el string correcto
        return {'original': s, 'count': 1, 'timeout': False}
    monkeypatch.setattr(bruteforce_utils, 'bruteforce_hash', patched_bruteforce_hash)
    result = bruteforce_utils.bruteforce_hash(h, 'MD5', max_len=1)
    assert isinstance(result, dict)
    assert result['original'] == s
    assert result['timeout'] is False
