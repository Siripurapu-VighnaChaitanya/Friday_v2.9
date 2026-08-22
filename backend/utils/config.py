import os
from dotenv import load_dotenv

# Load variables from .env file into os.environ
load_dotenv()

# ================= SECURE CONFIGURATION VARIABLES =================

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY")
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Optional: Add checks here to warn the user if a key is missing at boot
def check_configuration():
    missing_keys = []
    
    if not WEATHER_API_KEY: missing_keys.append("WEATHER_API_KEY")
    if not NEWS_API_KEY: missing_keys.append("NEWS_API_KEY")
    if not MAPBOX_API_KEY: missing_keys.append("MAPBOX_API_KEY")
    if not CURRENCY_API_KEY: missing_keys.append("CURRENCY_API_KEY")
    if not GROQ_API_KEY: missing_keys.append("GROQ_API_KEY")
        
    if missing_keys:
        print(f"⚠️ Warning: The following API keys are missing from your .env file: {', '.join(missing_keys)}")
        print("Certain web features will not work until you provide them.")
