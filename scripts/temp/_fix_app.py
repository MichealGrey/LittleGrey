import pathlib

f = pathlib.Path("e:/Proj/AIProj/LittleGrey/src/cli/app.py")
c = f.read_text(encoding="utf-8")

old_load = '''    def _load_history(self) -> None:
        history_path = self.config.resolve_path(
            self.config.memory.chat_history_path
        ) / "last_session.json"
        self.short_term.load(history_path)
'''

new_load = '''    def _load_history(self) -> None:
        history_path = self.config.resolve_path(
            self.config.memory.chat_history_path
        ) / "last_session.json"
        self.short_term.load(history_path)
        self.emotion._load_emotion_state(self.long_term)
        self.relationship._load_state()
'''

old_save = '''    def _save_history(self) -> None:
        history_path = self.config.resolve_path(
            self.config.memory.chat_history_path
        )
        history_path.mkdir(parents=True, exist_ok=True)
        self.short_term.save(history_path / "last_session.json")
'''

new_save = '''    def _save_history(self) -> None:
        history_path = self.config.resolve_path(
            self.config.memory.chat_history_path
        )
        history_path.mkdir(parents=True, exist_ok=True)
        self.short_term.save(history_path / "last_session.json")
        self.emotion._save_emotion_state(self.long_term)
        self.relationship._save_state()
'''

c = c.replace(old_load, new_load)
c = c.replace(old_save, new_save)
f.write_text(c, encoding="utf-8")
print("OK")
