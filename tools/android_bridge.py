import os, json, subprocess, webbrowser

def is_android():
    return "ANDROID_ARGUMENT" in os.environ or os.path.exists("/system/build.prop")

def _ctx():
    from jnius import autoclass
    return autoclass("org.kivy.android.PythonActivity").mActivity

def get_battery():
    try:
        r = subprocess.run(["termux-battery-status"], capture_output=True,
                           text=True, timeout=10)
        if r.returncode == 0:
            return f"Batterie: {json.loads(r.stdout).get('percentage', '?')}%"
    except Exception:
        pass
    try:
        with open("/sys/class/power_supply/battery/capacity") as f:
            return f"Batterie: {f.read().strip()}%"
    except OSError:
        pass
    if is_android():
        try:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            IF = autoclass("android.content.IntentFilter")
            BM = autoclass("android.os.BatteryManager")
            st = _ctx().registerReceiver(None, IF(Intent.ACTION_BATTERY_CHANGED))
            lv, sc = st.getIntExtra(BM.EXTRA_LEVEL, -1), st.getIntExtra(BM.EXTRA_SCALE, -1)
            if lv >= 0 and sc > 0:
                return f"Batterie: {int(lv*100/sc)}%"
        except Exception:
            pass
    return "Batterie illisible."

def send_sms(number, message):
    if is_android():
        try:
            from jnius import autoclass
            sm = autoclass("android.telephony.SmsManager").getDefault()
            parts = sm.divideMessage(str(message))
            if len(parts) > 1:
                sm.sendMultipartTextMessage(str(number), None, parts, None, None)
            else:
                sm.sendTextMessage(str(number), None, str(message), None, None)
            return f"SMS envoye a {number}."
        except Exception as e:
            return f"Erreur SMS: {e}"
    return "SMS non supporte ici."

def open_app(package):
    if is_android():
        for cmd in (["/system/bin/monkey", "-p", str(package),
                      "-c", "android.intent.category.LAUNCHER", "1"],
                    ["/system/bin/am", "start", "-n", f"{str(package)}/.MainActivity"]):
            try:
                if subprocess.run(cmd, capture_output=True, text=True,
                                   timeout=10).returncode == 0:
                    return f"{package} lancee."
            except Exception:
                continue
    return "Ouverture d'apps: Android uniquement."

def list_apps():
    if is_android():
        try:
            pkgs = _ctx().getPackageManager().getInstalledPackages(0)
            return "\n".join(pkgs.get(i).packageName for i in range(pkgs.size()))
        except Exception as e:
            return f"Erreur: {e}"
    return "Liste des apps: Android uniquement."

def open_url(url):
    if is_android():
        try:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            _ctx().startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(str(url))))
            return "URL ouverte."
        except Exception as e:
            return f"Erreur: {e}"
    webbrowser.open(str(url))
    return "URL ouverte."
