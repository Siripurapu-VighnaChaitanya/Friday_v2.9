# translator.py
from deep_translator import GoogleTranslator

def to_english(text):
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except:
        return text

def from_english(text, target_lang):
    try:
        return GoogleTranslator(source="en", target=target_lang).translate(text)
    except:
        return text
