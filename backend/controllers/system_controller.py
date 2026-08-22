# controllers/system_controller.py
import os
import subprocess
import re
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

def _get_volume_interface():
    """Helper to get the pycaw volume interface."""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except:
        return None

def set_volume(percent: int):
    """Sets system volume directly."""
    try:
        volume = _get_volume_interface()
        if volume:
            percent = max(0, min(100, percent))
            volume.SetMasterVolumeLevelScalar(percent / 100.0, None)
    except:
        pass

def volume_up():
    """Increase volume by 10%."""
    try:
        volume = _get_volume_interface()
        if volume:
            current = volume.GetMasterVolumeLevelScalar()
            volume.SetMasterVolumeLevelScalar(min(1.0, current + 0.1), None)
    except:
        pass

def volume_down():
    """Decrease volume by 10%."""
    try:
        volume = _get_volume_interface()
        if volume:
            current = volume.GetMasterVolumeLevelScalar()
            volume.SetMasterVolumeLevelScalar(max(0.0, current - 0.1), None)
    except:
        pass

def get_current_volume():
    """Returns current volume as 0-100."""
    try:
        volume = _get_volume_interface()
        if volume:
            return int(volume.GetMasterVolumeLevelScalar() * 100)
    except:
        pass
    return 50

# ================== NETWORK ==================

def _get_wifi_interface():
    try:
        output = subprocess.check_output('netsh interface show interface', shell=True).decode()
        for line in output.split('\n'):
            if "Wi-Fi" in line or "Wireless" in line:
                match = re.search(r'\w+\s+\w+\s+\w+\s+(.*)', line)
                if match: return match.group(1).strip()
    except: pass
    return "Wi-Fi"

def wifi(on: bool = True):
    interface = _get_wifi_interface()
    state = "enabled" if on else "disabled"
    os.system(f'netsh interface set interface "{interface}" {state}')

def bluetooth():
    os.system("start ms-settings:bluetooth")

def hotspot():
    os.system("start ms-settings:network-mobilehotspot")
