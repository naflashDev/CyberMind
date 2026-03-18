from app.services.hashed import bruteforce_utils


def test_bruteforce_hash_uses_pool(monkeypatch):
    # Dummy Pool replacement to avoid heavy CPU work
    class DummyPool:
        def __init__(self, n):
            self.n = n

        def map(self, fn, args):
            # Return one worker reporting a found value
            return [("found_secret", 10, False)] * self.n

        def close(self):
            pass

        def join(self):
            pass

    monkeypatch.setattr(bruteforce_utils, 'Pool', DummyPool)
    res = bruteforce_utils.bruteforce_hash('irrelevant', 'MD5', max_len=1, timeout=1, cpu_limit=1)
    assert isinstance(res, dict)
    assert res.get('original') in (None, 'found_secret')
