# command_listener.py
import speech_recognition as sr
import time
from services.ui_server import update_ui_state

recognizer = sr.Recognizer()

# ================= TUNED DEFAULTS =================
# These are overridden dynamically inside listen_for_command()
recognizer.pause_threshold = 0.8
recognizer.energy_threshold = 250
recognizer.dynamic_energy_threshold = False  # We control threshold manually for precision

from utils.constants import is_stop_command, is_cancel_command, is_exit_command, FRIDAY_PROMPTS

def listen_for_command(lang="en"):
    """
    Dual-mode listener:
      - While speaking: SHORT listen window, accepts STOP, CANCEL, and EXIT commands
      - Normal mode: Full listen window for any command
    """
    from services import tts
    was_speaking = tts.IS_SPEAKING

    with sr.Microphone() as source:

        # Only update UI to 'listening' if we are NOT currently speaking
        if not was_speaking:
            update_ui_state("listening")

        # ---- DYNAMIC SENSITIVITY ----
        if was_speaking:
            # HIGH threshold: must speak loudly to override Friday's voice
            recognizer.energy_threshold = 300
            recognizer.pause_threshold = 0.3
            recognizer.non_speaking_duration = 0.15
        else:
            # BALANCED threshold: sensitive but not picking up ambient room audio
            recognizer.energy_threshold = 200
            recognizer.pause_threshold = 0.75
            recognizer.non_speaking_duration = 0.4

        try:
            if was_speaking:
                # SHORT WINDOW — for interrupts (stop/cancel/exit)
                audio = recognizer.listen(
                    source,
                    timeout=3.5,
                    phrase_time_limit=3.5
                )
            else:
                # NORMAL COMMAND LISTEN
                audio = recognizer.listen(
                    source,
                    timeout=6,
                    phrase_time_limit=10
                )

        except sr.WaitTimeoutError:
            return None
        except Exception:
            return None

    try:
        # ---- RECOGNITION ----
        if lang == "te":
            text = recognizer.recognize_google(audio, language="te-IN").lower()
        elif lang == "hi":
            text = recognizer.recognize_google(audio, language="hi-IN").lower()
        else:
            # en-US has better accuracy than en-IN for general English
            text = recognizer.recognize_google(audio, language="en-US").lower()

        # Reject noise artifacts (less than 2 chars is not a real command)
        if not text or len(text.strip()) < 2:
            return None

        # ---- INTERRUPT DETECTION (while Friday is speaking) ----
        if was_speaking:
            if is_stop_command(text) or is_cancel_command(text) or is_exit_command(text):
                print(f"Interrupt command detected: '{text}'")
                return text
            else:
                # Ignore non-stop speech while Friday is speaking
                return None

        # ---- SELF-VOICE FILTER (while not speaking) ----
        if text:
            if any(prompt in text for prompt in FRIDAY_PROMPTS):
                print(f"Filtering self-voice echo: '{text}'")
                return None

        return text

    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        print("STT Request Error - check internet connection")
        return None
    except Exception:
        return None
