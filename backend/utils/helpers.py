from datetime import datetime
from services.tts import speak

def say_time_date():
    now = datetime.now()
    speak(f"The time is {now.strftime('%I:%M %p')}")
    speak(f"Today is {now.strftime('%A %d %B %Y')}")
