import os, json
from core.config import BASE_DIR, ensure_dirs

MEM = os.path.join(BASE_DIR, "memory.json")

class Memory:
    def __init__(self):
        ensure_dirs()
        try:
            with open(MEM, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except Exception:
            self.history = []

    def add(self, user, assistant):
        self.history.append({"u": user, "a": assistant})
        self.history = self.history[-20:]
        try:
            with open(MEM, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False)
        except Exception:
            pass

    def context(self, n=6):
        if not self.history:
            return "(debut de conversation)"
        return "\n".join(f"Toi: {e['u']}\nEVA: {e['a'][:200]}"
                         for e in self.history[-n:])
