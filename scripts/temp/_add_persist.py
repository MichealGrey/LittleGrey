import pathlib

f = pathlib.Path("e:/Proj/AIProj/LittleGrey/src/agent/emotion.py")
c = f.read_text(encoding="utf-8")

m = """
    def _save_emotion_state(self, long_term_memory: Any) -> None:
        if not long_term_memory:
            return
        try:
            recent_journals = [
                {
                    "timestamp": e.timestamp,
                    "emotion": e.emotion,
                    "intensity": e.intensity,
                    "secondary": e.secondary,
                    "trigger": e.trigger,
                    "summary": e.summary,
                }
                for e in self._mood_journal[-10:]
            ]
            long_term_memory.store(
                "emotion_state",
                metadata={
                    "type": "emotion_state",
                    "levels": self._levels.copy(),
                    "baseline": self._baseline.copy(),
                    "recent_journal": recent_journals,
                    "last_interaction_time": self._last_interaction_time,
                    "saved_at": time.time(),
                },
            )
        except Exception:
            pass

    def _load_emotion_state(self, long_term_memory: Any) -> None:
        if not long_term_memory:
            return
        try:
            results = long_term_memory.search("emotion_state", n=1)
            if not results:
                return
            data = results[0].get("metadata", {})
            saved_levels = data.get("levels")
            if saved_levels:
                for emo, val in saved_levels.items():
                    if emo in self._levels:
                        self._levels[emo] = max(0.0, min(1.0, float(val)))
            saved_baseline = data.get("baseline")
            if saved_baseline:
                for emo, val in saved_baseline.items():
                    if emo in self._baseline:
                        self._baseline[emo] = max(0.0, min(0.15, float(val)))
            recent_journal = data.get("recent_journal", [])
            for entry in recent_journal:
                mood_entry = MoodEntry(
                    timestamp=entry.get("timestamp", 0),
                    emotion=entry.get("emotion", "neutral"),
                    intensity=entry.get("intensity", 0.0),
                    secondary=entry.get("secondary"),
                    trigger=entry.get("trigger", "unknown"),
                    summary=entry.get("summary", ""),
                )
                self._mood_journal.append(mood_entry)
            saved_at = data.get("saved_at", 0)
            if saved_at > 0:
                elapsed = time.time() - saved_at
                decay_factor = max(0.0, 1.0 - (elapsed / 86400) * 0.5)
                for emo in self._levels:
                    self._levels[emo] *= decay_factor
        except Exception:
            pass
"""

lines = c.split(chr(10))
insert_idx = None
for i in range(len(lines) - 1, -1, -1):
    if "return self._snapshot()" in lines[i]:
        insert_idx = i + 1
        break

if insert_idx is not None:
    new_content = chr(10).join(lines[:insert_idx]) + chr(10) + m + chr(10).join(lines[insert_idx:])
    f.write_text(new_content, encoding="utf-8")
    print("OK")
else:
    print("FAIL")
