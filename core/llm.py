import requests
from core.config import get_key

TIMEOUT = 30

_OPENAI = [
    ("groq", "https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY", "llama-3.1-8b-instant"),
    ("openai", "https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY", "gpt-4o-mini"),
    ("mistral", "https://api.mistral.ai/v1/chat/completions", "MISTRAL_API_KEY", "mistral-small-latest"),
    ("deepseek", "https://api.deepseek.com/v1/chat/completions", "DEEPSEEK_API_KEY", "deepseek-chat"),
    ("openrouter", "https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY", "mistralai/mistral-7b-instruct:free"),
]

def _chat(url, key, model, prompt):
    r = requests.post(url, json={"model": model,
        "messages": [{"role": "user", "content": prompt}]},
        headers={"Authorization": f"Bearer {key}"}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def call_gemini(p):
    r = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
        json={"contents": [{"parts": [{"text": p}]}]},
        headers={"x-goog-api-key": get_key("GEMINI_API_KEY")}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

def call_anthropic(p):
    r = requests.post("https://api.anthropic.com/v1/messages",
        json={"model": "claude-3-5-haiku-latest", "max_tokens": 1500,
              "messages": [{"role": "user", "content": p}]},
        headers={"x-api-key": get_key("ANTHROPIC_API_KEY"),
                 "anthropic-version": "2023-06-01"}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["content"][0]["text"]

PROVIDERS = {}
for name, url, key, model in _OPENAI:
    PROVIDERS[name] = (lambda u, k, m: lambda p: _chat(u, k, m, p))(url, key, model)
PROVIDERS["gemini"] = call_gemini
PROVIDERS["anthropic"] = call_anthropic

_KEY_MAP = {n: k for n, (_u, _k, _m) in zip([n for n, _, _, _ in _OPENAI], _OPENAI)}
_KEY_MAP["gemini"] = "GEMINI_API_KEY"
_KEY_MAP["anthropic"] = "ANTHROPIC_API_KEY"

def available():
    return [n for n in PROVIDERS if get_key(_KEY_MAP[n])]

def route_llm(prompt):
    chain = available()
    if not chain:
        raise RuntimeError("Aucune cle API configuree (bouton Cfg).")
    errors = []
    for name in chain:
        try:
            return PROVIDERS[name](prompt)
        except requests.HTTPError as e:
            errors.append(f"{name}: HTTP {e.response.status_code}")
        except Exception as e:
            errors.append(f"{name}: {e}")
    raise RuntimeError("LLM echoue: " + " | ".join(errors))
