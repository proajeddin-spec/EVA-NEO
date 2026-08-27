import json, re
from core.llm import route_llm
from core.memory import Memory
from tools import search, android_bridge, files, skill_manager

class EVA:
    def __init__(self):
        self.memory = Memory()
        skill_manager.set_generator(self._gen_code)
        self.tools = {
            "search": search.search_web,
            "fetch": search.fetch_page,
            "battery": android_bridge.get_battery,
            "sms": android_bridge.send_sms,
            "open_app": android_bridge.open_app,
            "list_apps": android_bridge.list_apps,
            "open_url": android_bridge.open_url,
            "write_file": files.write_file,
            "read_file": files.read_file,
            "find_skill": skill_manager.find_or_create_skill,
            "run_skill": skill_manager.run_skill,
            "list_skills": skill_manager.list_skills,
        }

    def _gen_code(self, description):
        return route_llm(
            "Genere un script Python autonome (modules standard + requests). "
            "Definis une fonction main() qui RETOURNE une chaine. Pas de input(). "
            f"Tache: {description}\nCode uniquement, sans backticks.")

    def _action(self, resp):
        m = re.search(r'\{[^{}]*"tool"[^{}]*\}', resp, re.DOTALL)
        if m:
            try:
                a = json.loads(m.group(0))
                if isinstance(a, dict) and "tool" in a:
                    return a
            except json.JSONDecodeError:
                pass
        return None

    def process(self, user_input, max_steps=5):
        prompt = ("Tu es EVA, assistante IA sur Android. Outils: "
                  + ", ".join(self.tools)
                  + '. Pour agir, reponds UNIQUEMENT: {"tool": "nom", "args": {...}} '
                  "Sinon reponds en texte. Reponds en francais.\n---\nContexte:\n"
                  + self.memory.context() + f"\nToi: {user_input}")
        for _ in range(max_steps):
            try:
                resp = route_llm(prompt)
            except RuntimeError as e:
                return f"Erreur LLM: {e}"
            act = self._action(resp)
            if not act:
                self.memory.add(user_input, resp)
                return resp
            name = act["tool"]
            args = act.get("args", {}) or {}
            if name not in self.tools:
                prompt += f"\n[Outil '{name}' inconnu. Valides: {', '.join(self.tools)}]"
                continue
            try:
                result = self.tools[name](**args)
            except Exception as e:
                result = f"Erreur: {e}"
            prompt += f"\n[{name} -> {result}]\nReponds ou nouvelle action."
        final = route_llm(prompt + "\nReponse finale:")
        self.memory.add(user_input, final)
        return final
