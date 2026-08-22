# wake_word.py
import speech_recognition as sr
import time

from services.tts import IS_SPEAKING

r = sr.Recognizer()
r.dynamic_energy_threshold = False

# ================= WAKE WORD CONFIG =================
WAKE_PHRASES = [
    "hello friday",
    "hi friday",
    "hey friday",
    "friday",
    "ok friday",
]

WAKE_LOCKED = False
LAST_WAKE_TIME = 0
WAKE_COOLDOWN = 2

def reset_wake_lock():
    global WAKE_LOCKED
    WAKE_LOCKED = False


# ================= WAKE WORD LISTENER =================
def listen_for_wake_word():
    """
    Checks for wake-up trigger using voice wake word recognition.
    """
    global LAST_WAKE_TIME, WAKE_LOCKED

    if WAKE_LOCKED:
        return False

    while IS_SPEAKING:
        time.sleep(0.1)

    now = time.time()
    if now - LAST_WAKE_TIME < WAKE_COOLDOWN:
        return False

    # Listen for voice wake word via speech_recognition
    try:
        with sr.Microphone() as source:
            r.energy_threshold = 300
            r.pause_threshold = 0.6
            try:
                audio = r.listen(source, timeout=2, phrase_time_limit=4)
            except sr.WaitTimeoutError:
                return False

        # Try speech recognition
        text = r.recognize_google(audio, language="en-US").lower().strip()
        if any(phrase in text for phrase in WAKE_PHRASES):
            LAST_WAKE_TIME = time.time()
            WAKE_LOCKED = True
            print(f"Wake word detected: '{text}'")
            return True

    except (sr.UnknownValueError, sr.RequestError):
        pass
    except Exception:
        pass

    return False

