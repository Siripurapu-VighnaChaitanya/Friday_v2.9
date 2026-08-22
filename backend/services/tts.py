import threading
import tempfile
import os
import time
import pygame
import asyncio
import edge_tts
import re
from gtts import gTTS
from services.ui_server import update_ui_state

IS_SPEAKING = False
STOP_REQUESTED = False
_lock = threading.Lock()

# ================= VOICE MAPPING =================
VOICES = {
    "en": "en-US-GuyNeural",
    "te": "te-IN-MohanNeural",
    "hi": "hi-IN-MadhurNeural"
}

pygame.mixer.init()

# ================= STOP SPEAKING =================
def stop_speaking():
    global STOP_REQUESTED, IS_SPEAKING
    STOP_REQUESTED = True
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.unload() # Force unload on Windows to clear buffer
        IS_SPEAKING = False # Reset immediately to allow new commands
        update_ui_state("idle")
    except:
        pass

# ================= ASYNC EDGE-TTS HELPER =================
async def _generate_edge_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# ================= SPEAK =================
def speak(text, lang="en"):
    global IS_SPEAKING, STOP_REQUESTED

    if not text:
        return

    # 🛡️ CODE SAFETY GUARD
    # Automatically strip anything starting from triple backticks to the end
    # This prevents reading unclosed blocks or preamble text
    if "```" in text:
        text = text.split("```")[0].strip()
        if not text:
            text = "I have saved the code to your desktop."
    
    # Heuristic for naked code (missing backticks)
    lines = text.split("\n")
    clean_lines = []
    for line in lines:
        code_indicators = sum(1 for char in line if char in "{}();[]")
        # If a line looks like code, we cut the speech there
        if code_indicators > 3 and len(line) < 100:
            break
        clean_lines.append(line)
    
    text = "\n".join(clean_lines).replace("[CODE]", "").strip()
    
    if not text:
        text = "I have saved the code to your desktop."

    print("Friday:", text)

    IS_SPEAKING = True
    STOP_REQUESTED = False
    update_ui_state("thinking")  # Show "thinking" while audio is being generated

    def _run():
        global IS_SPEAKING, STOP_REQUESTED
        
        with _lock:
            audio_path = None
            try:
                # 1️⃣ CREATE TEMP FILE
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                    audio_path = f.name

                # 2️⃣ TRY EDGE-TTS (PREMIUM)
                success = False
                try:
                    voice = VOICES.get(lang, VOICES["en"])
                    asyncio.run(_generate_edge_tts(text, voice, audio_path))
                    success = True
                except Exception as e:
                    print(f"⚠️ Edge-TTS failed, falling back to gTTS: {e}")
                    success = False

                # 3️⃣ FALLBACK TO gTTS (STANDARD)
                if not success:
                    tts = gTTS(text=text, lang=lang)
                    tts.save(audio_path)

                # 4. PLAYBACK - Broadcast 'speaking' RIGHT when audio starts
                pygame.mixer.music.load(audio_path)
                update_ui_state("speaking", message=text)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    if STOP_REQUESTED:
                        pygame.mixer.music.stop()
                        break
                    time.sleep(0.05)
                
                if not STOP_REQUESTED:
                    time.sleep(1.2)  # Extended echo-settle buffer (was 0.6s)

            except Exception as e:
                print("❌ TTS Error:", e)

            finally:
                if audio_path and os.path.exists(audio_path):
                    try:
                        pygame.mixer.music.unload()
                        os.remove(audio_path)
                    except:
                        pass
                IS_SPEAKING = False
                update_ui_state("idle")

    threading.Thread(target=_run, daemon=True).start()

def wait_for_speech():
    """
    Blocks until Friday finishes speaking and adds a significant settlement delay.
    """
    while IS_SPEAKING:
        time.sleep(0.1)
    time.sleep(1.2) # Stronger buffer for Windows/Mic echo to prevent self-hearing
