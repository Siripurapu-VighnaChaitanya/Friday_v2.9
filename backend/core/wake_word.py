# wake_word.py
import speech_recognition as sr
import time
from services.tts import IS_SPEAKING

r = sr.Recognizer()
r.dynamic_energy_threshold = False  # Manual control for consistency

# ================= WAKE WORD CONFIG =================
# Accept multiple wake phrase variations for natural triggering
WAKE_PHRASES = [
    "hello friday",
    "hi friday",
    "hey friday",
    "friday",        # Single-word fallback
    "ok friday",
]

WAKE_LOCKED = False
LAST_WAKE_TIME = 0
WAKE_COOLDOWN = 2    # Reduced from 4s — allows faster re-triggering

def reset_wake_lock():
    """Call this AFTER language selection is done"""
    global WAKE_LOCKED
    WAKE_LOCKED = False

def listen_for_wake_word():
    global LAST_WAKE_TIME, WAKE_LOCKED

    # Already triggered, skip
    if WAKE_LOCKED:
        return False

    # Do not listen while speaking (avoids echo)
    while IS_SPEAKING:
        time.sleep(0.1)

    with sr.Microphone() as source:
        # Removed adjust_for_ambient_noise() — it adds 400ms delay every loop!
        # Instead, use a fixed balanced energy threshold.
        r.energy_threshold = 250
        r.pause_threshold = 0.5

        try:
            # Reduced timeout from 5 → 3s for faster loop cycling
            audio = r.listen(source, timeout=3, phrase_time_limit=4)
        except:
            return False

    try:
        text = r.recognize_google(audio, language="en-US").lower().strip()

        now = time.time()

        # Check if any wake phrase is in the detected text
        matched = any(phrase in text for phrase in WAKE_PHRASES)

        if matched:
            # Cooldown protection — prevents double-triggering
            if now - LAST_WAKE_TIME < WAKE_COOLDOWN:
                return False

            LAST_WAKE_TIME = now
            WAKE_LOCKED = True

            print(f"Wake word detected: '{text}'")
            return True

        return False

    except:
        return False
