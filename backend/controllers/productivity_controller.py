import psutil
import pyperclip

# ================== SYSTEM MONITOR ==================
def get_system_status():
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        bat_str = f"{battery.percent}%" if battery else "N/A"
        
        return f"System Status: CPU at {cpu}%, RAM at {ram}%, Battery at {bat_str}."
    except Exception as e:
        return f"Error checking system: {e}"

# ================== CLIPBOARD ==================
def read_clipboard():
    try:
        text = pyperclip.paste()
        if not text:
            return "The clipboard is empty."
        return f"The clipboard contains: {text[:100]}..." # Limit for TTS
    except Exception as e:
        return f"Error reading clipboard: {e}"
