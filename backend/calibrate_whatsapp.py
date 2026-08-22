"""
WhatsApp Call Button Calibration Tool
Run this with WhatsApp open on Amma's chat.
It will move the mouse to the estimated button position so you can verify.
"""
import pygetwindow as gw
import pyautogui
import ctypes
import time

# ---- DPI-AWARE COORDINATE CONVERSION ----
# pygetwindow returns LOGICAL coordinates (at 96 DPI baseline)
# pyautogui works in PHYSICAL pixels
# On 125% scaling: physical = logical * 1.25
dpi = ctypes.windll.user32.GetDpiForSystem()
SCALE = dpi / 96.0
print(f"DPI={dpi}, Scale={SCALE}x")
print(f"PyAutoGUI screen: {pyautogui.size()}")

wins = gw.getWindowsWithTitle('WhatsApp')
if not wins:
    print("WhatsApp is NOT open. Please open it first.")
    exit()

w = wins[0]
print(f"\nWhatsApp logical coords: left={w.left} top={w.top} w={w.width} h={w.height}")

# Convert logical window bounds to physical pixels for pyautogui
phys_left   = int(w.left   * SCALE)
phys_top    = int(w.top    * SCALE)
phys_right  = int((w.left + w.width)  * SCALE)
phys_height = int(w.height * SCALE)

print(f"Physical right edge: {phys_right}")
print(f"Physical top: {phys_top}")

# Header Y — the chat header bar is ~59px tall (at 96DPI), so ~74px at 125% scaling
header_y = phys_top + int(37 * SCALE)

# Button offsets from right edge (physical pixels)
# These are measured from actual WhatsApp Desktop UI
# Order from right: menu(⋮) → search → voice call → video call
positions = {
    "menu (⋮)":    phys_right - int(20  * SCALE),
    "search":      phys_right - int(50  * SCALE),
    "voice call ☎": phys_right - int(82  * SCALE),
    "video call 📷": phys_right - int(115 * SCALE),
}

print("\n--- Moving mouse to each button (3s each) ---")
print("Watch the screen to verify where the cursor lands!\n")

for name, x in positions.items():
    print(f"Moving to {name}: ({x}, {header_y})")
    pyautogui.moveTo(x, header_y, duration=0.5)
    time.sleep(3)

print("\nCalibration complete! Note which positions matched the buttons.")
