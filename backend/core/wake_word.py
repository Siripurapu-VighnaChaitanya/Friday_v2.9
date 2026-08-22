# wake_word.py
import speech_recognition as sr
import pyaudio
import struct
import time
from services.tts import IS_SPEAKING

r = sr.Recognizer()

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

# ================= REAL-TIME CLAP DETECTOR =================
class ClapDetector:
    def __init__(self, min_peak=5000, min_interval=0.12, max_interval=1.2):
        self.min_peak = min_peak
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.clap_count = 0
        self.last_clap_time = 0

    def process(self, peak, now=None):
        if now is None:
            now = time.time()

        # Reset if too much time passed since last clap (> 1.2s)
        if self.clap_count > 0 and (now - self.last_clap_time) > self.max_interval:
            self.clap_count = 0

        if peak >= self.min_peak:
            dt = now - self.last_clap_time
            if dt < self.min_interval:
                # Same single-clap reverberation, ignore
                return False

            if self.clap_count == 0:
                self.clap_count = 1
                self.last_clap_time = now
                print("👏 [Clap 1/3 detected]")
                return False
            elif 0.12 <= dt <= self.max_interval:
                self.clap_count += 1
                self.last_clap_time = now
                print(f"👏 [Clap {self.clap_count}/3 detected]")
                if self.clap_count >= 3:
                    self.clap_count = 0
                    return True
            else:
                self.clap_count = 1
                self.last_clap_time = now
                print("👏 [Clap 1/3 reset]")
                return False

        return False

# Persistent clap detector instance across loop cycles
_clap_detector = ClapDetector()

# ================= DUAL STREAMING WAKE LISTENER =================
def listen_for_wake_word():
    global LAST_WAKE_TIME, WAKE_LOCKED, _clap_detector

    if WAKE_LOCKED:
        return False

    while IS_SPEAKING:
        time.sleep(0.1)

    now = time.time()
    if now - LAST_WAKE_TIME < WAKE_COOLDOWN:
        return False

    # Audio stream parameters
    RATE = 16000
    CHUNK = 1024  # ~64ms chunks
    CYCLE_SECONDS = 3.0
    NUM_CHUNKS = int((RATE / CHUNK) * CYCLE_SECONDS)

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
        print(f"Mic init error in wake listener: {e}")
        if stream:
            try:
                stream.close()
            except:
                pass
        pa.terminate()
        time.sleep(0.5)
        return False

    speech_frames = []
    speaking_detected = False
    silence_chunks = 0

    try:
        for _ in range(NUM_CHUNKS):
            if IS_SPEAKING:
                break

            data = stream.read(CHUNK, exception_on_overflow=False)
            samples = struct.unpack(f'<{CHUNK}h', data)
            peak = max(abs(s) for s in samples)
            now = time.time()

            # 1️⃣ REAL-TIME CLAP CHECK (Immediate 0ms response!)
            if _clap_detector.process(peak, now):
                LAST_WAKE_TIME = now
                WAKE_LOCKED = True
                print("⚡ 3 Claps detected! Waking up...")
                return True

            # 2️⃣ SPEECH BUFFERING FOR WAKE PHRASES
            if peak > 1500:
                speaking_detected = True
                speech_frames.append(data)
                silence_chunks = 0
            elif speaking_detected:
                speech_frames.append(data)
                silence_chunks += 1
                # If ~450ms of silence after voice, proceed to speech recognition
                if silence_chunks >= 7:
                    break

    except Exception as e:
        pass
    finally:
        try:
            stream.stop_stream()
            stream.close()
        except:
            pass
        pa.terminate()

    # 3️⃣ SPEECH RECOGNITION (if speech was heard)
    if speech_frames and len(speech_frames) >= 4:
        try:
            raw_audio = b''.join(speech_frames)
            audio_data = sr.AudioData(raw_audio, RATE, 2)
            text = r.recognize_google(audio_data, language="en-US").lower().strip()

            if any(phrase in text for phrase in WAKE_PHRASES):
                now = time.time()
                LAST_WAKE_TIME = now
                WAKE_LOCKED = True
                print(f"Wake word detected: '{text}'")
                return True
        except:
            pass

    return False
