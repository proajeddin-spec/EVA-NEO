import os
from core.config import BASE_DIR, ensure_dirs

def _path(p):
    ensure_dirs()
    fdir = os.path.join(BASE_DIR, "files")
    os.makedirs(fdir, exist_ok=True)
    return p if os.path.isabs(p) else os.path.join(fdir, str(p))

def write_file(path, content):
    try:
        with open(_path(path), "w", encoding="utf-8") as f:
            f.write(str(content))
        return f"Ecrit: {path}"
    except OSError as e:
        return f"Erreur: {e}"

def read_file(path):
    try:
        with open(_path(path), "r", encoding="utf-8") as f:
            return f.read()[:4000]
    except OSError as e:
        return f"Erreur: {e}"

def list_files():
    ensure_dirs()
    try:
        items = os.listdir(os.path.join(BASE_DIR, "files"))
        return "\n".join(items) if items else "(vide)"
    except OSError:
        return "(vide)"
