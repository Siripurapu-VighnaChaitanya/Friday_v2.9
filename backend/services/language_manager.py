# language_manager.py
from services.tts import speak, wait_for_speech
from core.command_listener import listen_for_command

def choose_language():
    speak("Please choose language. English, Telugu, or Hindi.")
    wait_for_speech()

    while True:
        lang = listen_for_command("en")
        if not lang:
            continue

        # 🚀 FILTER OWN VOICE (Safety Check)
        if "please choose language" in lang or "please say" in lang:
            continue

        print("Language heard:", lang)

        if "english" in lang:
            speak("English selected")
            return "en"

        if "telugu" in lang:
            speak("తెలుగు ఎంచుకోబడింది", "te") # Telugu selected
            return "te"
            
        if "hindi" in lang:
            speak("हिंदी चुनी गई", "hi") # Hindi selected
            return "hi"

        speak("Please say English, Telugu, or Hindi.")
