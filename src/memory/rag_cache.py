from collections import OrderedDict
import time

class RAGCache:
    def __init__(self, max_size=64, ttl_seconds=300):
        self._cache = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

    def get(self, query):
        key = query.strip().lower()[:200]
        if key in self._cache:
            entry = self._cache[key]
            if time.monotonic() - entry[1] < self._ttl:
                self._hits += 1
                self._cache.move_to_end(key)
                return entry[0]
            else:
                del self._cache[key]
        self._misses += 1
        return None
    def put(self, query, result):
        key = query.strip().lower()[:200]
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
        self._cache[key] = (result, time.monotonic())

    def stats(self):
        t = self._hits + self._misses
        return dict(hits=self._hits, misses=self._misses, hit_rate=self._hits/t if t else 0.0, size=len(self._cache))