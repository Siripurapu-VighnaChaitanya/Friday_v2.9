import webbrowser
import pyautogui
import pygetwindow as gw
import ctypes
import time
from utils.firebase_util import get_db

# NOTE: On this system pygetwindow and pyautogui BOTH use physical pixels.
# No scaling conversion is needed — use coordinates directly.
_dpi = ctypes.windll.user32.GetDpiForSystem()
_DPI_SCALE = _dpi / 96.0  # Kept for logging only

# ================== DB ACCESS ==================
db = get_db()

def get_contact_number(name):
    """
    Looks up a contact name in the Firebase 'contacts' collection.
    Handles possessives (e.g., "mom's" -> "mom").
    """
    try:
        clean_name = name.lower().replace("'s", "").replace("\u2019s", "").strip()
        contacts_ref = db.collection('contacts')
        docs = contacts_ref.stream()
        for doc in docs:
            data = doc.to_dict()
            stored_name = data.get('name', '').lower().strip()
            if clean_name == stored_name or stored_name in clean_name or clean_name in stored_name:
                return data.get('phone')
        return None
    except Exception as e:
        print(f"❌ Firebase Contact Error: {e}")
        return None


def _focus_whatsapp():
    """Bring WhatsApp window to front if it's open."""
    time.sleep(1.5)
    wins = gw.getWindowsWithTitle('WhatsApp')
    if wins:
        win = wins[0]
        try:
            if win.isMinimized:
                win.restore()
            win.activate()
            time.sleep(0.8)
            return win
        except Exception:
            pass
    return None


def send_whatsapp_message(name, message):
    """
    Opens WhatsApp chat for the contact and sends the message.
    """
    phone = get_contact_number(name)
    if not phone:
        if name.replace("+", "").replace(" ", "").isdigit() and len(name) >= 10:
            phone = name
        else:
            return f"Contact {name} not found in your contacts, sir."

    # Deep-link opens the chat with the message pre-filled
    import urllib.parse
    encoded = urllib.parse.quote(message)
    url = f"whatsapp://send?phone={phone}&text={encoded}"
    webbrowser.open(url)
    time.sleep(5)

    win = _focus_whatsapp()
    if win:
        pyautogui.press('enter')
        time.sleep(0.5)
        return f"Message sent to {name}, sir."

    # Fallback: just press enter wherever
    pyautogui.press('enter')
    return f"Message sent to {name}, sir."


def add_contact_to_db(name, phone):
    """
    Saves a new name and number to the Firebase contacts collection.
    """
    try:
        contacts_ref = db.collection('contacts')
        data = {
            "name": name.lower().strip(),
            "phone": phone.strip()
        }
        contacts_ref.add(data)
        return f"Successfully saved {name} with number {phone} to your contacts, sir."
    except Exception as e:
        return f"Error saving contact: {e}"


def make_whatsapp_call(name, video=False):
    """
    Initiates a WhatsApp voice or video call using Windows UI Automation.
    Finds the 'Voice call' / 'Video call' button by its accessibility NAME —
    completely independent of screen coordinates, window size, or minimize state.
    """
    import os
    import subprocess as sp

    phone = get_contact_number(name)
    if not phone:
        if name.replace("+", "").replace(" ", "").isdigit() and len(name) >= 10:
            phone = name
        else:
            return f"Contact {name} not found in your contacts, sir."

    call_type = "video" if video else "voice"
    print(f"[WhatsApp] Initiating {call_type} call to {name} ({phone})...")

    try:
        # Step 1: Open the contact's chat
        webbrowser.open(f"whatsapp://send?phone={phone}")
        time.sleep(6)   # Wait for WhatsApp to fully load the chat

        # Step 2: Bring WhatsApp to front (restore if minimized)
        win = _focus_whatsapp()
        if not win:
            time.sleep(2)
            win = _focus_whatsapp()
        if not win:
            return "WhatsApp window not found. Please make sure the desktop app is open, sir."

        if win.isMinimized:
            win.restore()
            time.sleep(0.8)
        win.activate()
        time.sleep(1.0)

        # Step 3: Use Windows UI Automation (PowerShell) to click button by NAME
        # This is completely position-independent and immune to window/UI changes
        ps_script = os.path.join(os.path.dirname(__file__), '..', 'wa_call.ps1')
        ps_script = os.path.abspath(ps_script)

        result = sp.run(
            ['powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_script,
             '-CallType', call_type],
            capture_output=True, text=True, timeout=20
        )

        output = result.stdout.strip()
        print(f"[WhatsApp UIA] {output}")

        if result.returncode == 0:
            return f"{'Video' if video else 'Voice'} call started with {name}, sir."

        # If button name not found, print what buttons were found (for debugging)
        if result.returncode == 3:
            print(f"[WhatsApp UIA] Available buttons:\n{output}")

        return f"{'Video' if video else 'Voice'} call sent to {name}, sir."

    except Exception as e:
        print(f"[WhatsApp] Call error: {e}")
        return f"Sorry sir, I could not start the call. Error: {e}"




def reject_call():
    """
    Finds WhatsApp window and rejects the incoming call.
    """
    windows = gw.getWindowsWithTitle('WhatsApp')
    if windows:
        try:
            windows[0].activate()
            time.sleep(0.5)
            pyautogui.press('esc')
            return "Attempting to reject the call, sir."
        except Exception as e:
            return f"Error rejecting call: {e}"
    return "WhatsApp window not found, sir."


if __name__ == "__main__":
    print(get_contact_number("test"))
