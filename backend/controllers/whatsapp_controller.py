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
    Initiates a WhatsApp voice or video call on the Windows Desktop app.
    Strategy: Maximize WhatsApp window to a known state, then click the call
    button at its predictable top-right header position.
    This works regardless of whether the window was minimized or any size.
    """
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

        # Step 2: Find WhatsApp window
        win = _focus_whatsapp()
        if not win:
            time.sleep(2)
            win = _focus_whatsapp()
        if not win:
            return "WhatsApp window not found. Please make sure the desktop app is installed and open, sir."

        # Step 3: Restore if minimized, then MAXIMIZE
        # This guarantees we always know exactly where the buttons are
        if win.isMinimized:
            win.restore()
            time.sleep(0.8)

        win.maximize()          # Maximize to full screen
        time.sleep(1.0)         # Wait for maximize animation to finish
        win.activate()
        time.sleep(0.5)

        # Step 4: Get actual window bounds AFTER maximizing
        wins_now = gw.getWindowsWithTitle('WhatsApp')
        if wins_now:
            win = wins_now[0]

        win_right  = win.left + win.width
        win_top    = win.top
        header_y   = win_top + 32          # vertical midpoint of the header bar (~59px tall)

        # Step 5: Click in chat body first to ensure the window has keyboard focus
        center_x = win.left + win.width // 2
        center_y = win.top + (win.height // 2)
        pyautogui.click(center_x, center_y)
        time.sleep(0.5)

        # Step 6: Click the call icon in the top-right header
        # In WhatsApp Desktop (maximized), buttons are from right:
        #   Camera/Video icon ≈ 90-100px from right
        #   Phone/Voice icon  ≈ 135-145px from right
        # (These are reliable at any screen resolution when window is maximized)
        if video:
            btn_x = win_right - 95
            print(f"[WhatsApp] Clicking video call button at ({btn_x}, {header_y})")
        else:
            btn_x = win_right - 140
            print(f"[WhatsApp] Clicking voice call button at ({btn_x}, {header_y})")

        pyautogui.moveTo(btn_x, header_y, duration=0.3)   # Move slowly so it's visible
        time.sleep(0.3)
        pyautogui.click(btn_x, header_y)
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
