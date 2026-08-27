import os, json

HOME = os.path.expanduser("~")
CONFIG_PATH = os.path.join(HOME, "eva_config.json")
BASE_DIR = os.path.join(HOME, "eva")

def ensure_dirs():
    os.makedirs(os.path.join(BASE_DIR, "skills"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "files"), exist_ok=True)

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(cfg):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

def get_key(name):
    return load_config().get(name) or os.getenv(name, "")
