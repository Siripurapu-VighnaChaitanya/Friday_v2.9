# main.py
import time

from core.wake_word import listen_for_wake_word, reset_wake_lock, start_clap_detector
from core.command_listener import listen_for_command
from services.language_manager import choose_language
from core.mode_manager import handle_query
from services.tts import speak, stop_speaking, wait_for_speech   # ✅ stop control
from utils.constants import is_stop_command, is_cancel_command, is_exit_command
from services.ui_server import start_ui_server, update_ui_state, is_ui_connected
import webview
import threading

# ------------------ STATE ------------------
ACTIVE = False
LANGUAGE = None

# ------------------ BOOT ------------------
# Start the UI server immediately so the frontend can connect
start_ui_server()

def main_loop():
    global ACTIVE, LANGUAGE
    
    # Wait for the UI window to actually open and connect
    print("Waiting for UI to connect...")
    while not is_ui_connected():
        time.sleep(0.5)
        
    # Give the 3D model an extra second to render smoothly before speaking
    time.sleep(1.5)
    
    # Start background clap detection thread ONCE (runs independently of speech recognition)
    start_clap_detector()

    speak("Friday is running. Say hello friday or clap 3 times to wake me up.")
    wait_for_speech()

    # ⚡ TEST MODE: Skip wake word + secret code + language selection
    # Jump straight into active English mode for fast WhatsApp call testing
    ACTIVE = True
    LANGUAGE = "en"
    speak("Test mode. I am ready, sir. You can speak now.")
    wait_for_speech()

    while True:

        # ============== IDLE MODE (DISABLED IN TEST MODE) ==============
        if not ACTIVE:
            print("Listening for wake word...")
            wake_detected = listen_for_wake_word()

            if not wake_detected:
                time.sleep(0.5)
                continue
            print("Wake word detected")

            speak("Hello Chaitanya")
            speak("Access granted, sir.")
            time.sleep(0.4)

            LANGUAGE = "en"
            ACTIVE = True
            speak("I am ready, sir. You can speak now.", LANGUAGE)
            continue

        # ============== ACTIVE MODE ==============
        print("Listening for command...")
        # bridge.state("LISTENING", LANGUAGE)  # <-- Removed: tts.py now handles state transitions reliably
        query = listen_for_command(LANGUAGE)

        if not query:
            continue

        query = query.lower()
        print("User:", query)

        # -------- 🛑 IMMEDIATE INTERRUPT & CONTROL CHECKS --------

        if is_cancel_command(query):
            stop_speaking()
            # Clear pending state on soft cancel
            from core import offline_engine
            offline_engine.PENDING_CONFIRM = None
            offline_engine.PENDING_CODE_DATA = None
            
            ack = {
                "en": "Got it, sir. I'm listening again.",
                "te": "సరే సార్, నేను మళ్ళీ వింటున్నాను.",
                "hi": "ठीक है सर, मैं फिर से सुन रहा हूँ।"
            }
            speak(ack.get(LANGUAGE, ack["en"]), LANGUAGE)
            continue

        if is_stop_command(query):
            stop_speaking()   # 🔥 HARD STOP TTS
            from core import offline_engine
            offline_engine.PENDING_CONFIRM = None
            offline_engine.PENDING_CODE_DATA = None
            update_ui_state("idle")
            continue

        if is_exit_command(query):
            stop_speaking()   # stop any ongoing speech
            from core import offline_engine
            offline_engine.PENDING_CONFIRM = None
            offline_engine.PENDING_CODE_DATA = None
            
            sleep_msg = {
                "en": "Going back to sleep, sir. Say hello friday to wake me up.",
                "te": "నిద్రపోతున్నాను సార్. మళ్ళీ నన్ను లేపాలంటే హలో ఫ్రైడే అని పిలవండి.",
                "hi": "सो रहा हूँ सर। मुझे जगाने के लिए हेलो फ्राइडे कहें।"
            }
            speak(sleep_msg.get(LANGUAGE, sleep_msg["en"]), LANGUAGE)
            wait_for_speech()

            ACTIVE = False
            LANGUAGE = None

            reset_wake_lock()  # allow wake word again
            time.sleep(0.5)
            continue

        # -------- REAL QUERY: UPDATE UI TO THINKING --------
        update_ui_state("thinking", message=query)

        # -------- HANDLE QUERY --------
        try:
            handle_query(query, LANGUAGE)
            # wait_for_speech() is removed to allow "stop" detection during playback
        except Exception as e:
            print("Error handling query:", e)
            err_msg = {
                "en": "Sorry, something went wrong.",
                "te": "క్షమించండి, ఏదో తప్పు జరిగింది.",
                "hi": "माफ करना, कुछ गड़बड़ हो गई।"
            }
            speak(err_msg.get(LANGUAGE, err_msg["en"]), LANGUAGE)

if __name__ == "__main__":
    t = threading.Thread(target=main_loop, daemon=True)
    t.start()
    
    # Start the pywebview frontend on the main thread (blocking)
    import os
    index_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', '3d_avatar', 'index.html')
    webview.create_window('Friday', f'file://{index_path}', frameless=True, transparent=True, width=1400, height=900)
    webview.start()
