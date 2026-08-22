import os

START_MENU_PATHS = [
    r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    r"C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
]

def build_app_index():
    apps = {}
    for base in START_MENU_PATHS:
        base = os.path.expandvars(base)
        for root, _, files in os.walk(base):
            for f in files:
                if f.endswith(".lnk"):
                    apps[f.replace(".lnk", "").lower()] = os.path.join(root, f)
    return apps
