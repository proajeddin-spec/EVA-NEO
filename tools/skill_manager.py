import os, ast, sys, json, shutil, zipfile, tempfile, subprocess
from datetime import datetime, timezone
import requests
from core.config import BASE_DIR, ensure_dirs

SKILLS_DIR = os.path.join(BASE_DIR, "skills")
REGISTRY = os.path.join(SKILLS_DIR, "registry.json")
_G = None

def set_generator(fn):
    global _G
    _G = fn

def _load():
    try:
        with open(REGISTRY, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save(name, fp, desc, src, url=None):
    ensure_dirs()
    reg = _load()
    reg[name] = {"file": fp, "description": str(desc), "source": src,
                 "url": url, "date": datetime.now(timezone.utc).isoformat()}
    with open(REGISTRY, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)

def list_skills():
    reg = _load()
    return "\n".join(f"- {n} [{v['source']}]" for n, v in reg.items()) or "Aucun skill."

def search_github(query, n=5):
    try:
        r = requests.get("https://api.github.com/search/repositories",
                         params={"q": f"{query} language:python", "sort": "stars",
                                 "order": "desc", "per_page": n}, timeout=15)
        if r.status_code != 200:
            return []
        return r.json().get("items", [])
    except requests.RequestException:
        return []

def _dl(full_name, branch="main"):
    for br in (branch, "main", "master"):
        try:
            r = requests.get(f"https://codeload.github.com/{full_name}/zip/refs/heads/{br}", timeout=60)
            if r.status_code == 200:
                tmp = tempfile.mkdtemp(prefix="eva_")
                zp = os.path.join(tmp, "r.zip")
                with open(zp, "wb") as f:
                    f.write(r.content)
                with zipfile.ZipFile(zp) as zf:
                    root = zf.namelist()[0].split("/")[0]
                    zf.extractall(tmp)
                return os.path.join(tmp, root), tmp
        except Exception:
            continue
    return None, None

def _entry(d):
    for c in ("main.py", "skill.py", "app.py"):
        if os.path.exists(os.path.join(d, c)):
            return os.path.join(d, c)
    for root, _, files in os.walk(d):
        for f in files:
            if f.endswith(".py"):
                p = os.path.join(root, f)
                try:
                    with open(p, encoding="utf-8", errors="ignore") as fh:
                        if any(isinstance(n, ast.FunctionDef) and n.name == "main"
                               for n in ast.walk(ast.parse(fh.read()))):
                            return p
                except SyntaxError:
                    continue
    return None

def _install(repo, name=None):
    name = name or repo["full_name"].split("/")[-1].lower().replace(" ", "_")
    src, tmp = _dl(repo["full_name"], repo.get("default_branch", "main"))
    if not src:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
        return False, "Telechargement impossible."
    entry = _entry(src)
    if not entry:
        shutil.rmtree(tmp, ignore_errors=True)
        return False, "Pas de main() trouve."
    dest = os.path.join(SKILLS_DIR, name)
    os.makedirs(dest, exist_ok=True)
    for item in os.listdir(os.path.dirname(entry)):
        s = os.path.join(os.path.dirname(entry), item)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(dest, item))
    _save(name, os.path.join(dest, os.path.basename(entry)),
          repo.get("description") or "", "github", repo["html_url"])
    shutil.rmtree(tmp, ignore_errors=True)
    return True, f"installe depuis {repo['full_name']} ({repo['stargazers_count']} etoiles)"

def _create(desc, name=None):
    if not _G:
        return "Generateur LLM indisponible."
    try:
        code = _G(desc).replace("```python", "").replace("```", "").strip()
    except Exception as e:
        return f"Erreur generation: {e}"
    name = name or desc.lower().replace(" ", "_")[:30]
    ensure_dirs()
    path = os.path.join(SKILLS_DIR, f"{name}.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    _save(name, path, desc, "genere")
    return f"skill '{name}' cree localement."

def find_or_create_skill(description, skill_name=None):
    repos = search_github(description)
    if repos:
        best = repos[0]
        if best["stargazers_count"] >= 5 or best.get("description"):
            ok, msg = _install(best, skill_name)
            if ok:
                return f"[GITHUB] Skill '{msg}'"
            return f"[GitHub echoue: {msg}] -> creation...\n{_create(description, skill_name)}"
    return f"[CREE] {_create(description, skill_name)}"

def run_skill(skill_name, *args):
    reg = _load()
    if skill_name not in reg:
        return f"Skill '{skill_name}' introuvable. Disponibles: {list(reg) or 'aucun'}"
    fp = reg[skill_name]["file"]
    if not os.path.exists(fp):
        return "Fichier du skill manquant."
    try:
        r = subprocess.run([sys.executable, fp, *args], capture_output=True,
                           text=True, timeout=30, cwd=os.path.dirname(fp))
        return r.stdout.strip() if r.returncode == 0 else f"Erreur: {r.stderr.strip()[:300]}"
    except subprocess.TimeoutExpired:
        return "Timeout (30s)."
