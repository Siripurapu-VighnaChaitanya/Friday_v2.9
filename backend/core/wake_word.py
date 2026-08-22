# wake_word.py
import speech_recognition as sr
import time
import struct
import math
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
WAKE_COOLDOWN = 2    # Prevents double-triggering

def reset_wake_lock():
    """Call this AFTER language selection is done"""
    global WAKE_LOCKED
    WAKE_LOCKED = False

# ================= CLAP DETECTION ENGINE =================
def detect_3_claps(raw_data, sample_rate=16000, sample_width=2):
    """
    Analyzes raw PCM audio buffer to detect 3 sharp acoustic clap impulses.
    Gated by temporal spacing (140ms to 850ms between claps) to prevent
    false triggers from continuous noise, speech, or random tapping.
    """
    if not raw_data or len(raw_data) < sample_rate * sample_width * 0.3:
        return False
        
    num_samples = len(raw_data) // sample_width
    if num_samples == 0:
        return False
        
    samples = struct.unpack(f'<{num_samples}h', raw_data[:num_samples * sample_width])
    
    # 10ms frame analysis
    frame_len = int(sample_rate * 0.01)
    if frame_len <= 0:
        return False
        
    energies = []
    peaks = []
    for i in range(0, num_samples, frame_len):
        frame = samples[i:i+frame_len]
        if not frame:
            continue
        peak = max(abs(s) for s in frame)
        rms = math.sqrt(sum(s * s for s in frame) / len(frame))
        energies.append(rms)
        peaks.append(peak)
        
    if not energies:
        return False
        
    avg_energy = sum(energies) / len(energies)
    # Dynamic spike threshold
    threshold = max(5000, avg_energy * 3.0)
    
    clap_times = []
    last_clap_time = -1.0
    
    for idx, (rms, peak) in enumerate(zip(energies, peaks)):
        time_sec = idx * 0.01
        if peak > threshold and rms > threshold * 0.35:
            # Enforce 120ms lockout between spikes to ignore reverberations of a single clap
            if time_sec - last_clap_time > 0.12:
                clap_times.append(time_sec)
                last_clap_time = time_sec
                
    # Evaluate 3-clap timing pattern
    if len(clap_times) == 3:
        i1 = clap_times[1] - clap_times[0]
        i2 = clap_times[2] - clap_times[1]
        if 0.14 <= i1 <= 0.85 and 0.14 <= i2 <= 0.85:
            return True
            
    if len(clap_times) == 4:
        i1 = clap_times[1] - clap_times[0]
        i2 = clap_times[2] - clap_times[1]
        if 0.14 <= i1 <= 0.85 and 0.14 <= i2 <= 0.85:
            return True
            
    return False

# ================= DUAL WAKE LISTENER =================
def listen_for_wake_word():
    global LAST_WAKE_TIME, WAKE_LOCKED

    # Already triggered, skip
    if WAKE_LOCKED:
        return False

    # Do not listen while speaking (avoids echo)
    while IS_SPEAKING:
        time.sleep(0.1)

    with sr.Microphone() as source:
        r.energy_threshold = 250
        r.pause_threshold = 0.5

        try:
            audio = r.listen(source, timeout=3, phrase_time_limit=4)
        except:
            return False

    now = time.time()

    # 1️⃣ FAST OFFLINE 3-CLAP CHECK (0ms Latency)
    try:
        raw_pcm = audio.get_raw_data(convert_rate=16000, convert_width=2)
        if detect_3_claps(raw_pcm, sample_rate=16000, sample_width=2):
            if now - LAST_WAKE_TIME < WAKE_COOLDOWN:
                return False
            LAST_WAKE_TIME = now
            WAKE_LOCKED = True
            print("👏 3 Claps detected! Waking up...")
            return True
    except Exception as e:
        pass

    # 2️⃣ SPEECH WAKE WORD RECOGNITION ("hello friday", etc.)
    try:
        text = r.recognize_google(audio, language="en-US").lower().strip()

        matched = any(phrase in text for phrase in WAKE_PHRASES)

        if matched:
            if now - LAST_WAKE_TIME < WAKE_COOLDOWN:
                return False

            LAST_WAKE_TIME = now
            WAKE_LOCKED = True

            print(f"Wake word detected: '{text}'")
            return True

        return False

    except:
        return False
