import re, requests
from html.parser import HTMLParser

UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Mobile)"}

class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self._h, self._t = [], None, []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self._h, self._t = v, []
    def handle_data(self, d):
        if self._h is not None:
            self._t.append(d.strip())
    def handle_endtag(self, tag):
        if tag == "a" and self._h is not None:
            txt = " ".join(x for x in self._t if x)
            self.links.append((self._h, txt))
            self._h = None

def search_web(query, max_results=6):
    try:
        r = requests.post("https://lite.duckduckgo.com/lite/",
                          data={"q": query}, headers=UA, timeout=15)
        p = _Links()
        p.feed(r.text)
        out, seen = [], set()
        for href, txt in p.links:
            if href.startswith("http") and "duckduckgo.com" not in href and href not in seen:
                seen.add(href)
                out.append(f"- {(txt or href)[:80]} : {href}")
                if len(out) >= max_results:
                    break
        return "\n".join(out) or "Aucun resultat."
    except requests.RequestException as e:
        return f"Erreur recherche: {e}"

def fetch_page(url, max_chars=3000):
    try:
        r = requests.get(url, headers=UA, timeout=15)
        t = re.sub(r"<(script|style).*?</\1>", " ", r.text, flags=re.DOTALL | re.I)
        t = re.sub(r"<[^>]+>", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t[:max_chars] or "Page vide."
    except requests.RequestException as e:
        return f"Erreur: {e}"
