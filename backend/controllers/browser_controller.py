import os
import webbrowser
import pyautogui
import pygetwindow as gw
import time

# Common website mappings
WEBSITE_MAP = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://www.twitter.com",
    "github": "https://www.github.com",
    "stackoverflow": "https://www.stackoverflow.com",
    "gmail": "https://mail.google.com",
    "linkedin": "https://www.linkedin.com",
    "whatsapp": "https://web.whatsapp.com",
    "openai": "https://www.openai.com",
    "chatgpt": "https://chat.openai.com",
}

def open_website(query: str) -> bool:
    """
    Opens a website in Chrome.
    If the query is a known website name, use its URL.
    If it contains a dot (like 'openai.com'), use it as is.
    Otherwise, treat it as a potential domain and append '.com'.
    """
    query = query.lower().strip()
    
    # Remove the "website" suffix if present (English/Telugu/Hindi)
    suffixes = [
        " website", " వెబ్‌సైట్", " వెబ్ సైట్", " వెబ్సైట్", 
        " वेबसाइट", " वेब साईट", " वेब साइट"
    ]
    for suffix in suffixes:
        if query.endswith(suffix):
            query = query[:-len(suffix)].strip()
            break

    # 1. Check if it's a known website
    url = WEBSITE_MAP.get(query)
    
    # 2. If not known, check if it looks like a URL (contains a dot)
    if not url:
        if "." in query:
            if not query.startswith("http"):
                url = f"https://{query}"
            else:
                url = query
        else:
            # 3. If no dot, assume .com
            url = f"https://www.{(query.replace(' ', ''))}.com"

    try:
        # Use 'start chrome' to force Chrome on Windows
        os.system(f'start chrome "{url}"')
        return True
    except Exception as e:
        print(f"Error opening website: {e}")
        # Fallback to default browser if chrome fails
        try:
            webbrowser.open(url)
            return True
        except:
            return False

def close_website(website_name: str = None):
    """
    Closes a specific tab in Chrome using Ctrl+Tab to search and Ctrl+W to close.
    """
    try:
        # If no specific name, just close current active tab
        if not website_name:
            pyautogui.hotkey('ctrl', 'w')
            return "Closing the active website tab."

        website_name = website_name.lower().strip()
        
        # Find all Chrome windows
        chrome_windows = [w for w in gw.getWindowsWithTitle('Chrome') if 'Google Chrome' in w.title]
        
        if not chrome_windows:
            return "No Chrome windows found."

        # Search through ALL Chrome windows
        for chrome_win in chrome_windows:
            try:
                if chrome_win.isMinimized:
                    chrome_win.restore()
                chrome_win.activate()
                time.sleep(0.5)
            except:
                pass

            # Try to find the tab in this window (max 20 tabs)
            for _ in range(20):
                try:
                    active_win = gw.getActiveWindow()
                    # Verify we are in A Chrome window (any Chrome window is fine for cycling)
                    if not active_win or "Chrome" not in str(active_win.title):
                        try: chrome_win.activate()
                        except: pass
                        time.sleep(0.3)
                        active_win = gw.getActiveWindow()

                    if active_win and "Chrome" in str(active_win.title):
                        current_title = str(active_win.title).lower()
                        if website_name in current_title:
                            pyautogui.hotkey('ctrl', 'w')
                            return f"Closed {website_name} tab."
                    
                    # Switch to next tab
                    pyautogui.hotkey('ctrl', 'tab')
                    time.sleep(0.4) 
                except Exception as win_e:
                    print(f"Window interaction warning: {win_e}")
                    pyautogui.hotkey('ctrl', 'tab')
                    time.sleep(0.4)
            
        return f"Could not find a tab named {website_name} in any Chrome window."

    except Exception as e:
        print(f"Error closing website: {e}")
        return "Sorry, I could not close the website tab."
def search_query(query: str):
    """
    Performs a Google search for the given query.
    """
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    try:
        os.system(f'start chrome "{url}"')
        return f"Searching for {query} on Google."
    except Exception as e:
        webbrowser.open(url)
        return f"Searching for {query}."
