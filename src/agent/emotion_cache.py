from collections import OrderedDict

class EmotionCache:
    def __init__(self, max_size=128, threshold=0.85):
        self._cache = OrderedDict()
        self._max_size = max_size
        self._threshold = threshold
        self._hits = 0
        self._misses = 0
    def get(self, text):
        key = text.strip().lower()[:200]
        if key in self._cache:
            self._hits += 1
            self._cache.move_to_end(key)
            return self._cache[key]
        for ck, result in self._cache.items():
            if self._sim(key, ck) >= self._threshold:
                self._hits += 1
                self._cache.move_to_end(ck)
                return result
        self._misses += 1
        return None
    def put(self, text, result):
        key = text.strip().lower()[:200]
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache[key] = result
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = result
    def _sim(self, t1, t2):
        if t1 == t2: return 1.0
        s1, s2 = set(t1), set(t2)
        u = s1 | s2
        return len(s1 & s2) / len(u) if u else 0.0

    def stats(self):
        t = self._hits + self._misses
        return dict(hits=self._hits, misses=self._misses, hit_rate=self._hits/t if t else 0.0, size=len(self._cache))