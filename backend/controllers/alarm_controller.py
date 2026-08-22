import os
import time
import pyautogui
import re

# Enable PyAutoGUI fail-safe (moving mouse to corner of screen aborts the script)
pyautogui.FAILSAFE = True

def parse_time(time_str):
    """
    Extracts hour, minute, and am/pm from a spoken time string.
    Handles '7:00 a.m.', '11:00 p.m.', '7:00 a.', '11:00 p.', '7 am', '11 pm',
    '6:30 in the morning', '10 at night', '19:30', Telugu/Hindi time phrases, etc.
    """
    try:
        s = str(time_str).lower().strip()
        
        # Check PM indicators
        is_pm = bool(re.search(
            r'\b(pm|p\.m\.|p\.m|night|evening|afternoon)\b|(?:\b|\d\s*)p\b|సాయంత్రం|రాత్రి|మధ్యాహ్నం|शाम|रात|दोपहर',
            s
        ))
        # Check AM indicators
        is_am = bool(re.search(
            r'\b(am|a\.m\.|a\.m|morning)\b|(?:\b|\d\s*)a\b|ఉదయం|सुबह',
            s
        ))

        clean = re.sub(r'[^0-9:]', ' ', s)
        parts = [p for p in clean.split() if p]
        if not parts:
            return None, None, None
            
        time_part = parts[0]
        if ':' in time_part:
            h_str, m_str = time_part.split(':', 1)
        else:
            h_str = time_part
            m_str = parts[1] if len(parts) > 1 and len(parts[1]) <= 2 else '00'
            
        h = int(h_str)
        m = int(m_str) if m_str.isdigit() else 0
        
        if h >= 24 or m >= 60:
            return None, None, None
            
        if h == 0:
            h = 12
            ampm = 'am'
        elif h > 12:
            h = h - 12
            ampm = 'pm'
        elif h == 12:
            ampm = 'pm' if not is_am else 'am'
        else:
            if is_pm:
                ampm = 'pm'
            elif is_am:
                ampm = 'am'
            else:
                ampm = 'am'  # default to am
                
        minute_str = f'{m:02d}'
        hour_str = str(h)
        return hour_str, minute_str, ampm
    except Exception:
        return None, None, None

def set_windows_alarm(target_time_str):
    """
    Opens the Windows 'Alarms & Clock' application and uses keyboard automation
    to create a new alarm safely.
    Handles AM/PM and potential exceptions.
    """
    try:
        hour, minute, ampm = parse_time(target_time_str)
        if not hour:
            return "I could not understand the time you provided for the alarm."
            
        # 1. Open Windows Clock App
        os.system("start ms-clock:")
        
        # 2. Wait heavily for app load
        time.sleep(3.5) 
        
        # 3. Predictable Start State (Force Maximize)
        # Alt+Space opens the window menu, 'x' selects Maximize. 
        # This is much more reliable than Win+Up and never snaps or minimizes.
        pyautogui.hotkey('alt', 'space')
        time.sleep(0.5)
        pyautogui.press('x') 
        time.sleep(1.0)
        
        screen_width, screen_height = pyautogui.size()
        
        # 4. Force Switch to "Alarm" Tab
        # In a maximized display, the sidebar is on the left.
        # "Alarm" is the 3rd item down. 
        # Previously y=220 hit the 4th item (Stopwatch). So we adjust y up by around 55 pixels to hit the 3rd item (Alarm).
        pyautogui.click(80, 165)
        time.sleep(1.0)

        
        # 5. Click the 'Add' (+) button
        # Click the "+" button (roughly 50 pixels left from the right edge, and 80 pixels up from the bottom to avoid the taskbar)
        pyautogui.click(screen_width - 50, screen_height - 90)
        time.sleep(1.5) # Wait for the new alarm modal to slide up
        
        # 6. Type HH:MM:AM/PM
        # In the Windows 11 modal, the focus is placed automatically on the hour box when you create a new alarm.
        pyautogui.write(hour, interval=0.1)
        time.sleep(0.4)
        
        pyautogui.press('tab') # move to minutes column
        time.sleep(0.4)
        pyautogui.write(minute, interval=0.1)
        time.sleep(0.4)
        
        pyautogui.press('tab') # move to AM/PM column
        time.sleep(0.4)
        
        # In Windows Clock, typing 'a' selects AM, 'p' selects PM.
        if ampm == "pm":
            pyautogui.write('p')
        else:
            pyautogui.write('a')
            
        time.sleep(0.5)
        
        # 7. Save the alarm
        # Hitting Enter inside the AM/PM box might not always work. 
        # Tabbing twice safely lands on the "Save" button in Win 11!
        # From AM/PM -> Tab -> Alarm name -> Tab -> Repeat -> Tab -> Days ... wait that's too long.
        # Let's just try Enter, and Ctrl+S again.
        pyautogui.hotkey('ctrl', 's')
        time.sleep(0.5)
        pyautogui.press('enter')
        
        # 8. Close the application
        time.sleep(1.0) # Wait a second for the app to finish saving the alarm
        pyautogui.hotkey('alt', 'f4')
        
        return f"I have set an alarm for {hour}:{minute} {ampm}, sir."
        
    except pyautogui.FailSafeException:
        # User moved mouse to corner to abort
        return "Alarm creation aborted by user."
    except Exception as e:
        return f"Failed to set alarm due to automatic UI error: {e}"
