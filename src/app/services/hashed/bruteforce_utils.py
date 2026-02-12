
"""
@file bruteforce_utils.py
@author naflashDev
@brief Utilities for hash type detection and brute-force cracking (CPU y soporte experimental GPU).
@details Provides functions to detect hash type and perform brute-force attacks using multiprocessing (CPU) o GPU (cupy) si está disponible. El uso de GPU es experimental y solo se activa si cupy está instalado y hay GPU compatible.
"""

# GPU detection must be outside the docstring to be available globally

cp = None
try:
    import cupy as _cp
    cp = _cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

import hashlib
import string
import itertools
from multiprocessing import Pool, cpu_count
from typing import Optional, Tuple

# Most common special characters for brute force
SPECIAL_CHARS = '!@#$%^&*()-_=+[]{};:,.<>/?|\\'
ALL_CHARS = string.ascii_letters + string.digits + SPECIAL_CHARS

HASH_LENGTHS = {
    32: 'MD5',
    64: 'SHA256',
    128: 'SHA512',
}

HASH_FUNCTIONS = {
    'MD5': lambda s: hashlib.md5(s.encode()).hexdigest(),
    'SHA256': lambda s: hashlib.sha256(s.encode()).hexdigest(),
    'SHA512': lambda s: hashlib.sha512(s.encode()).hexdigest(),
}

def detect_hash_type(hash_str: str) -> Optional[str]:
    '''
    @brief Detect hash type by length and allowed chars.
    @param hash_str Hash string to analyze.
    @return Hash type as string (MD5, SHA256, SHA512) or None if unknown.
    '''
    l = len(hash_str)
    return HASH_LENGTHS.get(l)

def _bruteforce_worker(args: Tuple[str, str, int, int, int, float, int]) -> Tuple[Optional[str], int, bool]:
    '''
    @brief Worker for brute-force: tries all combinations in a chunk, with timeout and count.
    @param hash_str Hash to crack.
    @param hash_type Hash type (MD5, SHA256, SHA512).
    @param min_len Minimum length.
    @param max_len Maximum length.
    @param chunk_idx Index of the chunk for multiprocessing.
    @param time_limit Timestamp (epoch) when to stop.
    @param max_combinations Max combinations to try (for safety, optional, can be 0 for unlimited).
    @return (original string if found, count, timeout_reached)
    '''
    import time
    hash_str, hash_type, min_len, max_len, chunk_idx, time_limit, max_combinations = args
    chars = ALL_CHARS
    hash_func = HASH_FUNCTIONS[hash_type]
    import os
    n_chunks = int(os.environ.get("BRUTEFORCE_N_CHUNKS", cpu_count()))
    chunk_size = (len(chars) + n_chunks - 1) // n_chunks  # ceil division
    start = chunk_idx * chunk_size
    end = min(len(chars), (chunk_idx + 1) * chunk_size)
    count = 0
    import time as _time
    for length in range(min_len, max_len + 1):
        for prefix in chars[start:end]:
            for comb in itertools.product(chars, repeat=length-1):
                if _time.time() > time_limit:
                    return None, count, True
                candidate = prefix + ''.join(comb)
                count += 1
                if max_combinations and count >= max_combinations:
                    return None, count, True
                if hash_func(candidate) == hash_str:
                    return candidate, count, False
                # Reduce CPU usage solo si longitud > 1
                if length > 1 and count % 1000 == 0:
                    _time.sleep(0.01)  # Sleep 10ms cada 1000 combinaciones
    return None, count, False

def bruteforce_hash(hash_str: str, hash_type: str, max_len: int = 20, timeout: int = 60, cpu_limit: int = 0, gpu_limit: int = 0) -> dict:
    '''
    @brief Brute-force a hash using multiprocessing (CPU) or GPU (cupy) if available, with timeout and count.

    Tries to crack the hash. Stops after timeout seconds. Returns dict with result, count, timeout.
    If GPU is available (cupy), uses GPU for parallel hash checking (experimental).

    @param hash_str Hash to crack.
    @param hash_type Hash type (MD5, SHA256, SHA512).
    @param max_len Maximum length to try.
    @param timeout Timeout in seconds (default 120).
    @param cpu_limit Max CPU cores to use (0 = all available)
    @param gpu_limit Max GPU usage (experimental, 0 = sin límite)
    @return dict: {'original': str|None, 'count': int, 'timeout': bool}
    '''
    import time
    min_len = 1
    time_limit = time.time() + timeout

    # Validate hash_type before proceeding (avoid KeyError in workers)
    if hash_type not in HASH_FUNCTIONS:
        # Return a controlled result for invalid hash type
        return {'original': None, 'count': 0, 'timeout': False, 'error': f'Invalid hash type: {hash_type}'}

    # --- GPU branch (experimental, solo para hashes cortos y max_len <= 6) ---
    if GPU_AVAILABLE and max_len <= 6 and hash_type in ("MD5", "SHA256", "SHA512"):
        try:
            # Solo para combinaciones pequeñas, para evitar OOM
            chars = ALL_CHARS
            for length in range(min_len, max_len + 1):
                # Generar todas las combinaciones posibles (¡cuidado con RAM/GPU!)
                import itertools
                combos = [''.join(c) for c in itertools.product(chars, repeat=length)]
                batch_size = 100000  # Procesar en lotes para no agotar memoria
                for i in range(0, len(combos), batch_size):
                    if time.time() > time_limit:
                        return {'original': None, 'count': i, 'timeout': True}
                    batch = combos[i:i+batch_size]
                    # Limitar uso de GPU si se especifica (experimental, solo si cupy soporta limitación)
                    # (En la práctica, cupy no limita, pero aquí se deja el parámetro para futuro soporte)
                    arr = cp.array(batch)
                    if hash_type == "MD5":
                        hashes = cp.asarray([cp.hash.hexdigest(cp.hash.md5(s.encode())) for s in arr])
                    elif hash_type == "SHA256":
                        hashes = cp.asarray([cp.hash.hexdigest(cp.hash.sha256(s.encode())) for s in arr])
                    elif hash_type == "SHA512":
                        hashes = cp.asarray([cp.hash.hexdigest(cp.hash.sha512(s.encode())) for s in arr])
                    else:
                        continue
                    # Buscar coincidencia
                    matches = cp.where(hashes == hash_str)[0]
                    if matches.size > 0:
                        idx = int(matches[0].get())
                        return {'original': batch[idx], 'count': i+idx+1, 'timeout': False}
            return {'original': None, 'count': len(combos), 'timeout': False}
        except Exception as e:
            # Si falla, fallback a CPU
            pass

    # --- CPU branch (por defecto) ---
    # Limitar núcleos de CPU si se especifica
    # Por defecto, limitar a 2 núcleos salvo que cpu_limit se especifique
    default_cpus = 2
    n_cpus = default_cpus if cpu_limit <= 0 else min(cpu_limit, cpu_count())
    import os
    # Pasar el número de chunks a los workers vía variable de entorno
    os.environ["BRUTEFORCE_N_CHUNKS"] = str(n_cpus)
    pool = Pool(n_cpus)
    args = [(hash_str, hash_type, min_len, max_len, i, time_limit, 0) for i in range(n_cpus)]
    results = pool.map(_bruteforce_worker, args)
    pool.close()
    pool.join()
    total_count = 0
    timeout_reached = False
    found = None
    for r, count, timeout_flag in results:
        total_count += count
        if r:
            found = r
        if timeout_flag:
            timeout_reached = True
    return {'original': found, 'count': total_count, 'timeout': timeout_reached}
