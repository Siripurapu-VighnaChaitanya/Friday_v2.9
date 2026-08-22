import webbrowser
import pyautogui
import pygetwindow as gw
import time
import os
from utils.firebase_util import get_db

# ================== DB ACCESS ==================
db = get_db()

def get_contact_number(name):
    """
    Looks up a contact name in the Firebase 'contacts' collection.
    Handles possessives (e.g., "mom's" -> "mom").
    """
    try:
        # 1. Clean name (remove 's, 's, etc.)
        clean_name = name.lower().replace("'s", "").replace("'s", "").strip()
        
        contacts_ref = db.collection('contacts')
        docs = contacts_ref.stream()
        for doc in docs:
            data = doc.to_dict()
            stored_name = data.get('name', '').lower().strip()
            # 2. Check for exact or partial match
            if clean_name == stored_name or stored_name in clean_name or clean_name in stored_name:
                return data.get('phone')
        return None
    except Exception as e:
        print(f"❌ Firebase Contact Error: {e}")
        return None

def send_whatsapp_message(name, message):
    """
    Opens WhatsApp chat for the contact and types the message.
    """
    phone = get_contact_number(name)
    if not phone:
        # If name not found, check if 'name' is already a phone number
        if name.isdigit() and len(name) >= 10:
            phone = name
        else:
            return f"Contact {name} not found."

    url = f"whatsapp://send?phone={phone}&text={message}"
    webbrowser.open(url)
    time.sleep(4)  # Wait for app to open and load chat
    
    # Focus and Send
    windows = gw.getWindowsWithTitle('WhatsApp')
    if windows:
        win = windows[0]
        try:
            if win.isMinimized: win.restore()
            win.activate()
            time.sleep(1)
            pyautogui.press('enter')
            return f"Message sent to {name}."
        except:
            pass
            
    # Fallback press if window detection is weird
    pyautogui.press('enter')
    return f"Message sent to {name}."

def add_contact_to_db(name, phone):
    """
    Saves a new name and number to the Firebase contacts collection.
    """
    try:
        contacts_ref = db.collection('contacts')
        
        # Add the contact
        data = {
            "name": name.lower().strip(),
            "phone": phone.strip()
        }
        contacts_ref.add(data)
        return f"Successfully saved {name} with number {phone} to your contacts."
    except Exception as e:
        return f"Error saving contact: {e}"

def make_whatsapp_call(name, video=False):
    """
    Opens chat and uses hotkeys to start a call.
    """
    phone = get_contact_number(name)
    if not phone:
        if name.isdigit() and len(name) >= 10:
            phone = name
        else:
            return f"Contact {name} not found."

    # Open chat
    print(f"DEBUG: Opening WhatsApp URI for {name} ({phone})")
    webbrowser.open(f"whatsapp://send?phone={phone}")
    time.sleep(6) # Give it plenty of time to load the chat

    # Focus window
    print("DEBUG: Searching for WhatsApp window...")
    all_whatsapp_windows = [w for w in gw.getWindowsWithTitle('WhatsApp')]
    
    target_win = None
    for win in all_whatsapp_windows:
        if win.title == "WhatsApp" or "WhatsApp" in win.title:
            target_win = win
            break

    if target_win:
        print(f"DEBUG: Found window: {target_win.title}")
        try:
            if target_win.isMinimized:
                target_win.restore()
            
            target_win.activate()
            time.sleep(1.0)
            
            # --- STEP 1: OPEN CHAT ---
            # Ensure we are in the chat first
            webbrowser.open(f"whatsapp://send?phone={phone}")
            time.sleep(6) # Give it plenty of time to load
            
            # --- STEP 2: FOCUS AND OPEN MENU ---
            target_win.activate()
            time.sleep(1.0)
            
            # Click the "Call" button in the header
            # Based on your screenshot, it's roughly 180-200px from the right
            win_right = target_win.left + target_win.width
            header_y = target_win.top + 50
            call_btn_x = win_right - 190
            
            print(f"DEBUG: Clicking Call Menu button at {call_btn_x}, {header_y}")
            pyautogui.click(call_btn_x, header_y)
            time.sleep(1.5) # Wait for menu to pop up
            
            # --- STEP 3: SELECT VOICE/VIDEO ---
            if video:
                # Video is usually to the right of Voice in the menu
                pyautogui.press('right')
                time.sleep(0.5)
                pyautogui.press('enter')
            else:
                # Voice is usually highlighted by default
                pyautogui.press('enter')
                
            # --- STEP 4: HOTKEY BACKUP ---
            time.sleep(1.0)
            pyautogui.hotkey('ctrl', 'shift', 'c' if not video else 'v')
                
            return f"Call sequence completed for {name}."
        except Exception as e:
            print(f"DEBUG: Call Error: {e}")
            return f"Error: {e}"
        except Exception as e:
            print(f"DEBUG: Call Error: {e}")
            return f"Error during call attempt: {e}"
            
    return "WhatsApp window not found. Please make sure the desktop app is open."

def reject_call():
    """
    Finds WhatsApp window and presses the reject button (hotkey/image).
    """
    windows = gw.getWindowsWithTitle('WhatsApp')
    if windows:
        windows[0].activate()
        # For Desktop app, 'Esc' often rejects or ends an incoming call UI if focused
        pyautogui.press('esc')
        return "Attempting to reject call."
    return "WhatsApp window not found."

if __name__ == "__main__":
    # Test
    print(get_contact_number("test"))
