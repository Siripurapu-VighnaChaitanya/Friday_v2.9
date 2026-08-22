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
    Initiates a WhatsApp voice or video call.
    Strategy:
      1. Open the contact chat via whatsapp://send
      2. Bring WhatsApp to foreground using win32gui (NO mouse click on buttons)
      3. Click once in the SAFE CENTRE of the chat panel (large area, never misses)
      4. Press Escape to clear the text input focus
      5. Send Ctrl+Shift+C (voice) or Ctrl+Shift+V (video) — official WA Desktop shortcuts
    """
    import win32gui
    import win32con

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
        time.sleep(6)   # Wait for chat to fully load

        # Step 2: Bring WhatsApp to front WITHOUT any mouse clicking
        # Use win32gui directly so we don't accidentally click on anything
        hwnd = win32gui.FindWindow(None, 'WhatsApp')
        if hwnd:
            if win32gui.IsIconic(hwnd):                   # Minimized?
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.8)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(1.0)
        else:
            # Fallback to pygetwindow
            win = _focus_whatsapp()
            if not win:
                return "WhatsApp window not found. Please make sure the app is open, sir."

        # Step 3: Get window geometry for a SAFE click in the chat message area
        wins = gw.getWindowsWithTitle('WhatsApp')
        if not wins:
            return "WhatsApp window lost after focus, sir."
        w = wins[0]

        # Click at 65% of width (right panel / chat area) x 55% of height (message area)
        # This is a LARGE, reliable area — never lands on sidebar, header, or input box
        safe_x = w.left + int(w.width  * 0.65)
        safe_y = w.top  + int(w.height * 0.55)
        print(f"[WhatsApp] Clicking chat body at ({safe_x}, {safe_y}) to set focus...")
        pyautogui.click(safe_x, safe_y)
        time.sleep(0.5)

        # Step 4: Press Escape to exit the message text input box focus
        pyautogui.press('escape')
        time.sleep(0.4)

        # Step 5: Send the official WhatsApp Desktop keyboard shortcut
        #   Ctrl+Shift+C = Voice call
        #   Ctrl+Shift+V = Video call
        if video:
            print("[WhatsApp] Sending Ctrl+Shift+V (video call shortcut)...")
            pyautogui.hotkey('ctrl', 'shift', 'v')
        else:
            print("[WhatsApp] Sending Ctrl+Shift+C (voice call shortcut)...")
            pyautogui.hotkey('ctrl', 'shift', 'c')

        time.sleep(1.0)
        return f"{'Video' if video else 'Voice'} call started with {name}, sir."

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
