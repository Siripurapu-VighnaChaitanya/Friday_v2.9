import webbrowser
import pyautogui
import pygetwindow as gw
import time
import subprocess
from utils.firebase_util import get_db

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
    Initiates a WhatsApp voice or video call using deep-link URIs.
    Primary method: whatsapp://call or whatsapp://videocall URI
    Fallback: open chat then use keyboard shortcut Ctrl+Shift+C/V
    """
    phone = get_contact_number(name)
    if not phone:
        if name.replace("+", "").replace(" ", "").isdigit() and len(name) >= 10:
            phone = name
        else:
            return f"Contact {name} not found in your contacts, sir."

    call_type = "video" if video else "audio"
    print(f"[WhatsApp] Initiating {call_type} call to {name} ({phone})...")

    # ---- STRATEGY 1: Direct WhatsApp call URI ----
    # These URIs directly open WhatsApp and initiate the call dialog
    if video:
        call_uri = f"whatsapp://videocall?phone={phone}"
    else:
        call_uri = f"whatsapp://call?phone={phone}"

    try:
        webbrowser.open(call_uri)
        time.sleep(5)  # Give WhatsApp time to open and load call screen

        # Try to focus and confirm any "Allow" dialog if it appears
        win = _focus_whatsapp()
        if win:
            # Press Enter to confirm any permission dialog
            pyautogui.press('enter')
            time.sleep(0.5)
            return f"{'Video' if video else 'Voice'} call started with {name}, sir."
        
        return f"{'Video' if video else 'Voice'} call initiated with {name}, sir."

    except Exception as e:
        print(f"[WhatsApp] URI call error: {e}")

    # ---- STRATEGY 2: Open chat then use keyboard shortcut ----
    print("[WhatsApp] Falling back to keyboard shortcut method...")
    try:
        webbrowser.open(f"whatsapp://send?phone={phone}")
        time.sleep(6)

        win = _focus_whatsapp()
        if not win:
            return "WhatsApp window not found. Please make sure the desktop app is open, sir."

        # Keyboard shortcut: Ctrl+Shift+C for voice, Ctrl+Shift+V for video
        if video:
            pyautogui.hotkey('ctrl', 'shift', 'v')
        else:
            pyautogui.hotkey('ctrl', 'shift', 'c')

        time.sleep(1.5)
        return f"{'Video' if video else 'Voice'} call shortcut sent to {name}, sir."

    except Exception as e:
        print(f"[WhatsApp] Keyboard fallback error: {e}")
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
