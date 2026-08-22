# app_controller.py
import os
import difflib   # 🔴 FUZZY: new import
from services.app_indexer import build_app_index
from services.tts import speak
from controllers.browser_controller import open_website

# ================== LOAD APPS ==================
APP_INDEX = build_app_index()

# ================== 🔴 SPOKEN ALIASES ==================
APP_ALIASES = {
    # VS Code
    "vs code": "visual studio code",
    "vscode": "visual studio code",
    "visual code": "visual studio code",

    # Microsoft Apps
    "ms word": "word",
    "ms excel": "excel",
    "ms powerpoint": "powerpoint",

    # Copilot (common mishearing)
    "ko pilot": "copilot",
    "co pilot": "copilot",
    "copilot": "copilot",
}

# ================== 🔴 LANGUAGE → ENGLISH MAP ==================
LANG_APP_MAP = {
    # ---------- Telugu ----------
    "వాట్సాప్": "whatsapp",
    "ఫైల్ మేనేజర్": "file manager",
    "ఫైల్ ఎక్స్ప్లోరర్": "file explorer",
    "క్రోమ్": "chrome",
    "క్యాలిక్యులేటర్": "calculator",
    "కెమెరా": "camera",
    "నోట్ప్యాడ్": "notepad",

    # ---------- Hindi ----------
    "व्हाट्सएप": "whatsapp",
    "फाइल मैनेजर": "file manager",
    "फाइल एक्सप्लोरर": "file explorer",
    "क्रोम": "chrome",
    "कैलकुलेटर": "calculator",
    "कैमरा": "camera",
    "नोटपैड": "notepad",
}

# ================== SYSTEM APPS (OPEN) ==================
SYSTEM_APPS = {
    "notepad": "notepad",
    "file manager": "explorer",
    "file explorer": "explorer",
    "explorer": "explorer",
    "camera": "start microsoft.windows.camera:",
    "calculator": "calc",
    "settings": "start ms-settings:",
    "task manager": "taskmgr",
    "whatsapp": "start whatsapp:",
    "chrome": "start chrome"
}

# ================== PROCESS MAP (CLOSE) ==================
APP_PROCESS_MAP = {
    "whatsapp": "WhatsApp.exe",
    "chrome": "chrome.exe",
    "camera": "WindowsCamera.exe",
    "calculator": "CalculatorApp.exe",
    "task manager": "Taskmgr.exe",
    "notepad": "notepad.exe",
    "word": "WINWORD.EXE",
    "excel": "EXCEL.EXE",
    "powerpoint": "POWERPNT.EXE"
}

# ================== NORMALIZE APP NAME ==================
def normalize_app_name(spoken: str) -> str:
    spoken = spoken.lower().strip()

    # 1️⃣ Language map (Telugu / Hindi)
    for local_name, english_name in LANG_APP_MAP.items():
        if local_name in spoken:
            return english_name

    # 2️⃣ Spoken aliases (vs code, ms word, etc.)
    for alias, canonical in APP_ALIASES.items():
        if alias in spoken:
            return canonical

    return spoken

# ================== 🔴 FUZZY MATCH HELPER ==================
def fuzzy_match(spoken: str, choices, cutoff=0.6):
    """
    Returns best fuzzy match or None
    """
    matches = difflib.get_close_matches(
        spoken, choices, n=1, cutoff=cutoff
    )
    return matches[0] if matches else None


# ================== OPEN APP ==================
def open_app(spoken, lang, msg):
    spoken = normalize_app_name(spoken)

    # 1️⃣ EXACT SYSTEM APP
    if spoken in SYSTEM_APPS:
        os.system(SYSTEM_APPS[spoken])
        speak(msg("open_app", lang, app=spoken), lang)
        return True

    # 2️⃣ 🔴 FUZZY SYSTEM APP
    sys_match = fuzzy_match(spoken, SYSTEM_APPS.keys())
    if sys_match:
        os.system(SYSTEM_APPS[sys_match])
        speak(msg("open_app", lang, app=sys_match), lang)
        return True

    # 3️⃣ START MENU APPS (exact)
    for app_name, shortcut in APP_INDEX.items():
        if spoken in app_name:
            os.startfile(shortcut)
            speak(msg("open_app", lang, app=spoken), lang)
            return True

    # 4️⃣ 🔴 FUZZY START MENU APPS
    app_names = list(APP_INDEX.keys())
    match = fuzzy_match(spoken, app_names)
    if match:
        os.startfile(APP_INDEX[match])
        speak(msg("open_app", lang, app=match), lang)
        return True

    speak(msg("app_not_found", lang), lang)
    return False


# ================== CLOSE APP ==================
def close_app(spoken, lang, msg):
    spoken = normalize_app_name(spoken)

    # 🔴 SAFE FILE MANAGER CLOSE (NO BLACK SCREEN)
    if spoken in ("file manager", "file explorer", "explorer"):
        os.system(
            'powershell -Command "(New-Object -ComObject Shell.Application).Windows() '
            '| ForEach-Object {$_.Quit()}"'
        )
        speak(msg("close_app", lang, app=spoken), lang)
        return True

    exe = APP_PROCESS_MAP.get(spoken)

    # 🔴 FUZZY CLOSE MATCH
    if not exe:
        exe_key = fuzzy_match(spoken, APP_PROCESS_MAP.keys())
        if exe_key:
            exe = APP_PROCESS_MAP[exe_key]
            spoken = exe_key

    # UWP / STORE APPS
    if spoken in ("whatsapp", "camera", "microsoft store"):
        os.system(
            f'powershell -Command "Get-Process | '
            f'Where-Object {{$_.ProcessName -like \\"*{spoken}*\\"}} | '
            f'Stop-Process -Force"'
        )
        speak(msg("close_app", lang, app=spoken), lang)
        return True

    if exe:
        os.system(f'taskkill /f /im "{exe}"')
        speak(msg("close_app", lang, app=spoken), lang)
        return True

    speak(msg("app_not_found", lang), lang)
    return False
