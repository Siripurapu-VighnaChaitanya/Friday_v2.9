# wake_word.py
import speech_recognition as sr
import pyaudio
import struct
import time
import threading

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


# ================= CLAP BACKGROUND THREAD =================
# Runs continuously in the background and sets a flag when 3 claps are heard.
# This NEVER conflicts with speech_recognition's microphone usage.

_clap_triggered = threading.Event()   # Set when 3 claps detected
_clap_thread_active = False

def _clap_listener_thread():
    """Background thread that listens ONLY for 3 claps using a persistent PyAudio stream."""
    RATE = 16000
    CHUNK = 1024  # ~64ms at 16kHz
    MIN_PEAK = 5000
    MIN_INTERVAL = 0.13    # 130ms minimum between claps
    MAX_INTERVAL = 1.2     # 1.2s max between claps (reset if exceeded)

    pa = pyaudio.PyAudio()
    stream = None
    try:
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
    except Exception as e:
        print(f"[ClapDetector] Could not open mic stream: {e}")
        pa.terminate()
        return

    clap_count = 0
    last_clap_time = 0.0

    print("[ClapDetector] Background clap thread started.")

    while _clap_thread_active:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
        except Exception:
            time.sleep(0.05)
            continue

        if IS_SPEAKING:
            # Don't detect claps while Friday is speaking (avoid false triggers)
            clap_count = 0
            continue

        samples = struct.unpack(f'<{CHUNK}h', data)
        peak = max(abs(s) for s in samples)
        now = time.time()

        # --- Reset if too long since last clap ---
        if clap_count > 0 and (now - last_clap_time) > MAX_INTERVAL:
            clap_count = 0

        # --- Detect a sharp transient ---
        if peak >= MIN_PEAK:
            dt = now - last_clap_time
            if dt < MIN_INTERVAL:
                continue   # Reverberation of same clap, ignore

            if clap_count == 0:
                clap_count = 1
                last_clap_time = now
                print("👏 [Clap 1/3]")
            elif 0.13 <= dt <= MAX_INTERVAL:
                clap_count += 1
                last_clap_time = now
                print(f"👏 [Clap {clap_count}/3]")
                if clap_count >= 3:
                    clap_count = 0
                    print("⚡ 3 Claps detected! Waking up...")
                    _clap_triggered.set()
            else:
                clap_count = 1
                last_clap_time = now
                print("👏 [Clap 1/3 (reset)]")

    try:
        stream.stop_stream()
        stream.close()
    except:
        pass
    pa.terminate()
    print("[ClapDetector] Background clap thread stopped.")


def start_clap_detector():
    """Start the persistent background clap detection thread. Call once at startup."""
    global _clap_thread_active
    _clap_thread_active = True
    t = threading.Thread(target=_clap_listener_thread, daemon=True)
    t.start()


def stop_clap_detector():
    global _clap_thread_active
    _clap_thread_active = False


# ================= WAKE WORD LISTENER =================
def listen_for_wake_word():
    """
    Checks for wake-up trigger (clap OR speech).
    Uses speech_recognition for voice and a background thread for claps.
    Both run independently without interfering.
    """
    global LAST_WAKE_TIME, WAKE_LOCKED

    if WAKE_LOCKED:
        return False

    while IS_SPEAKING:
        time.sleep(0.1)

    now = time.time()
    if now - LAST_WAKE_TIME < WAKE_COOLDOWN:
        return False

    # --- 1. Check if background clap thread already triggered ---
    if _clap_triggered.is_set():
        _clap_triggered.clear()
        LAST_WAKE_TIME = time.time()
        WAKE_LOCKED = True
        return True

    # --- 2. Try voice wake word via speech_recognition ---
    try:
        with sr.Microphone() as source:
            r.energy_threshold = 300
            r.pause_threshold = 0.6
            try:
                audio = r.listen(source, timeout=2, phrase_time_limit=4)
            except sr.WaitTimeoutError:
                # While waiting for speech, also check for claps
                if _clap_triggered.is_set():
                    _clap_triggered.clear()
                    LAST_WAKE_TIME = time.time()
                    WAKE_LOCKED = True
                    return True
                return False

        # Check clap flag one more time (may have triggered during recording)
        if _clap_triggered.is_set():
            _clap_triggered.clear()
            LAST_WAKE_TIME = time.time()
            WAKE_LOCKED = True
            return True

        # Try speech recognition
        text = r.recognize_google(audio, language="en-US").lower().strip()
        if any(phrase in text for phrase in WAKE_PHRASES):
            LAST_WAKE_TIME = time.time()
            WAKE_LOCKED = True
            print(f"Wake word detected: '{text}'")
            return True

    except (sr.UnknownValueError, sr.RequestError):
        # Check clap one last time on voice failure
        if _clap_triggered.is_set():
            _clap_triggered.clear()
            LAST_WAKE_TIME = time.time()
            WAKE_LOCKED = True
            return True
    except Exception:
        pass

    return False
