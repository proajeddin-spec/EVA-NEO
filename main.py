import os
import sys
import threading
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

from core.config import load_config, save_config

def _log_path():
    try:
        if platform == "android":
            from jnius import autoclass
            ctx = autoclass("org.kivy.android.PythonActivity").mActivity
            d = ctx.getExternalFilesDir(None)
            if d:
                return os.path.join(d.getAbsolutePath(), "eva_log.txt")
        return os.path.join(os.path.expanduser("~"), "eva_log.txt")
    except Exception:
        return os.path.join(os.path.expanduser("~"), "eva_log.txt")

def log(msg):
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass

log("=== EVA demarrage ===")

FIELDS = [
    ("GROQ_API_KEY", "Groq (gratuit)", "console.groq.com"),
    ("GEMINI_API_KEY", "Google Gemini", "aistudio.google.com"),
    ("OPENAI_API_KEY", "OpenAI", "platform.openai.com"),
    ("MISTRAL_API_KEY", "Mistral", "console.mistral.ai"),
    ("DEEPSEEK_API_KEY", "DeepSeek", "platform.deepseek.com"),
    ("ANTHROPIC_API_KEY", "Anthropic (Claude)", "console.anthropic.com"),
    ("OPENROUTER_API_KEY", "OpenRouter", "openrouter.ai"),
]

KV = '''
ScreenManager:
    ChatScreen:
        id: chat_screen

<ChatScreen>:
    name: "chat"
    BoxLayout:
        orientation: "vertical"
        padding: 8
        spacing: 5
        ScrollView:
            id: scroller
            do_scroll_y: True
            Label:
                id: chat_log
                text: "EVA prete. Ecris ton message ci-dessous.\\n\\n"
                text_size: self.width - 10, None
                size_hint_y: None
                height: max(self.texture_size[1], 1)
                halign: "left"
                valign: "top"
        BoxLayout:
            size_hint_y: None
            height: "48dp"
            spacing: 5
            Button:
                text: "Cfg"
                size_hint_x: None
                width: "48dp"
                on_release: app.open_config()
            Button:
                text: "Mic"
                size_hint_x: None
                width: "48dp"
                on_release: app.start_voice()
            TextInput:
                id: msg_input
                multiline: False
                hint_text: "Message a EVA..."
                on_text_validate: app.send_message(self.text)
            Button:
                text: "OK"
                size_hint_x: None
                width: "48dp"
                on_release: app.send_message(msg_input.text)
'''

VOICE_RC = 52465

class ConfigScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "config"
        self.fields = {}
        layout = BoxLayout(orientation="vertical", padding=15, spacing=8)
        layout.add_widget(Label(text="Configuration EVA", font_size="22sp",
                                size_hint_y=None, height="40dp"))
        layout.add_widget(Label(text="Entre au moins une cle API.",
                                font_size="13sp", size_hint_y=None, height="30dp"))
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=8, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for key_name, label, hint in FIELDS:
            grid.add_widget(Label(text=f"{label}  ({hint})", font_size="13sp",
                                  size_hint_y=None, height="24dp"))
            ti = TextInput(multiline=False, password=True, write_tab=False,
                           size_hint_y=None, height="44dp", hint_text=key_name)
            self.fields[key_name] = ti
            grid.add_widget(ti)
        scroll.add_widget(grid)
        layout.add_widget(scroll)
        btn = Button(text="Sauvegarder et demarrar",
                     size_hint_y=None, height="48dp")
        btn.bind(on_release=lambda *_: App.get_running_app().save_keys())
        layout.add_widget(btn)
        self.add_widget(layout)

class ChatScreen(Screen):
    pass

class EVAApp(App):
    title = "EVA"

    def build(self):
        log("build() commence")
        self.agent = None
        try:
            self.sm = Builder.load_string(KV)
            self.sm.add_widget(ConfigScreen())
            cfg = load_config()
            if any(cfg.get(k) for k, _, _ in FIELDS):
                self.sm.current = "chat"
                Clock.schedule_once(lambda dt: self._init_async(), 0.5)
            else:
                self.sm.current = "config"
        except Exception:
            log(f"build ERREUR: {traceback.format_exc()}")
        return self.sm if hasattr(self, "sm") else ScreenManager()

    def save_keys(self):
        log("save_keys clique")
        try:
            if platform == "android":
                try:
                    from android.permissions import request_permissions, Permission
                    request_permissions([Permission.INTERNET, Permission.SEND_SMS])
                except Exception as e:
                    log(f"permissions: {e}")
            scr = self.sm.get_screen("config")
            cfg = {k: scr.fields[k].text.strip() for k, _, _ in FIELDS}
            save_config({k: v for k, v in cfg.items() if v})
            self.sm.current = "chat"
            self._append("Initialisation d'EVA en cours...")
            Clock.schedule_once(lambda dt: self._init_async(), 0.2)
        except Exception:
            err = traceback.format_exc()
            log(f"save_keys ERREUR: {err}")
            self._append(f"Erreur sauvegarde:\n{err}")

    def _init_async(self):
        def worker():
            try:
                log("Import core.agent...")
                from core.agent import EVA
                log("Creation EVA()...")
                self.agent = EVA()
                log("EVA cree OK")
                Clock.schedule_once(
                    lambda dt: self._append("EVA initialisee. Envoie un message!"), 0)
            except Exception:
                err = traceback.format_exc()
                log(f"init ERREUR:\n{err}")
                Clock.schedule_once(
                    lambda dt: self._append(f"Erreur init EVA:\n{err[-500:]}"), 0)
        threading.Thread(target=worker, daemon=True).start()

    def open_config(self):
        try:
            cfg = load_config()
            scr = self.sm.get_screen("config")
            for k, _, _ in FIELDS:
                scr.fields[k].text = cfg.get(k, "")
            self.sm.current = "config"
        except Exception as e:
            log(f"open_config: {e}")

    def _append(self, txt):
        try:
            scr = self.sm.get_screen("chat")
            scr.ids.chat_log.text += txt + "\n\n"
            Clock.schedule_once(
                lambda dt: setattr(scr.ids.scroller, "scroll_y", 0), 0)
        except Exception as e:
            log(f"_append: {e}")

    def start_voice(self):
        if platform != "android":
            self._append("Vocal disponible uniquement sur Android.")
            return
        try:
            from jnius import autoclass
            from android import activity as android_activity
            Intent = autoclass("android.content.Intent")
            RI = autoclass("android.speech.RecognizerIntent")
            PA = autoclass("org.kivy.android.PythonActivity")
            intent = Intent(RI.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(RI.EXTRA_LANGUAGE_MODEL, RI.LANGUAGE_MODEL_FREE_FORM)
            intent.putExtra(RI.EXTRA_LANGUAGE, "fr-FR")
            try:
                android_activity.unbind(on_activity_result=self._on_voice)
            except Exception:
                pass
            android_activity.bind(on_activity_result=self._on_voice)
            PA.mActivity.startActivityForResult(intent, VOICE_RC)
        except Exception as e:
            log(f"voice: {e}")
            self._append(f"Erreur vocal: {e}")

    def _on_voice(self, rc, result_code, data):
        if rc != VOICE_RC:
            return
        if result_code != -1 or data is None:
            self._append("(non reconnu)")
            return
        try:
            from jnius import autoclass
            RI = autoclass("android.speech.RecognizerIntent")
            results = data.getStringArrayListExtra(RI.EXTRA_RESULTS)
            if results and results.size() > 0:
                self.send_message(results.get(0))
        except Exception as e:
            log(f"voice result: {e}")

    def send_message(self, msg):
        msg = (msg or "").strip()
        if not msg:
            return
        try:
            self.sm.get_screen("chat").ids.msg_input.text = ""
            self._append(f"Toi: {msg}")
            if not self.agent:
                self._append("EVA pas encore prete, patiente...")
                self._init_async()
                return
            self._append("...")
            threading.Thread(target=self._worker, args=(msg,),
                             daemon=True).start()
        except Exception as e:
            log(f"send_message: {e}")

    def _worker(self, msg):
        try:
            resp = self.agent.process(msg)
        except Exception as e:
            resp = f"Erreur: {e}"
        Clock.schedule_once(lambda dt: self._finish(resp), 0)

    def _finish(self, resp):
        try:
            cl = self.sm.get_screen("chat").ids.chat_log
            if cl.text.endswith("...\n\n"):
                cl.text = cl.text[: -len("...\n\n")]
            self._append(f"EVA: {resp}")
        except Exception as e:
            log(f"_finish: {e}")

EVAApp().run()
