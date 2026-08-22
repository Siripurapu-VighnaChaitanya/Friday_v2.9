# offline_engine.py
import os
import re
import datetime
from PIL import ImageGrab
from controllers.system_controller import (
    set_volume,
    volume_up,
    volume_down,
    wifi,
    bluetooth,
    hotspot
)
from services.tts import speak, stop_speaking
from controllers.app_controller import open_app, close_app   # ✅ NEW IMPORT

# ================== GLOBAL STATE ==================
PENDING_CONFIRM = None
PENDING_CODE_DATA = None

# ================== LANGUAGE MESSAGES ==================
MESSAGES = {
    "open_app": {
        "en": "Opening {app}, sir.",
        "te": "{app} ఓపెన్ చేస్తున్నాను సార్.",
        "hi": "{app} खोल रहा हूँ सर।"
    },
    "close_app": {
        "en": "Closing {app}, sir.",
        "te": "{app} మూసేస్తున్నాను సార్.",
        "hi": "{app} बंद कर रहा हूँ सर।"
    },
    "app_not_found": {
        "en": "I could not find that application, sir.",
        "te": "ఆ యాప్ నాకు కనిపించలేదు సార్.",
        "hi": "मुझे वह ऐप नहीं मिला सर।"
    },
    "time": {
        "en": "The time is {value}, sir.",
        "te": "ఇప్పుడు సమయం {value}, సార్.",
        "hi": "अभी समय {value} है सर।"
    },
    "date": {
        "en": "Today's date is {value}, sir.",
        "te": "ఈ రోజు తేదీ {value}, సార్.",
        "hi": "आज की तारीख {value} है सर।"
    },
    "day": {
        "en": "Today is {value}, sir.",
        "te": "ఈ రోజు {value}, సార్.",
        "hi": "आज {value} है सर।"
    },
    "screenshot": {
        "en": "Screenshot taken, sir.",
        "te": "స్క్రీన్ షాట్ తీసాను సార్.",
        "hi": "स्क्रीनशॉट लिया गया सर।"
    },
    "wifi_on": {
        "en": "WiFi turned on, sir.",
        "te": "వైఫై ఆన్ చేశాను సార్.",
        "hi": "वाईफाई चालू कर दिया सर।"
    },
    "wifi_off": {
        "en": "WiFi turned off, sir.",
        "te": "వైఫై ఆఫ్ చేశాను సార్.",
        "hi": "वाईफाई बंद कर दिया सर।"
    },
    "bluetooth": {
        "en": "Opening Bluetooth settings, sir.",
        "te": "బ్లూటూత్ సెట్టింగ్స్ ఓపెన్ చేస్తున్నాను సార్.",
        "hi": "ब्लूटूथ सेटिंग्स खोल रहा हूँ सर।"
    },
    "hotspot": {
        "en": "Opening Hotspot settings, sir.",
        "te": "హాట్‌స్పాట్ సెట్టింగ్స్ ఓపెన్ చేస్తున్నాను సార్.",
        "hi": "हॉटस्पॉट सेटिंग्स खोल रहा हूँ सर।"
    },
    "volume_set": {
        "en": "Volume set to {value} percent, sir.",
        "te": "వాల్యూమ్ {value} శాతానికి సెట్ చేశాను సార్.",
        "hi": "वॉल्यूम {value} प्रतिशत पर सेट किया सर।"
    },
    "volume_up": {
        "en": "Volume increased, sir.",
        "te": "వాల్యూమ్ పెంచాను సార్.",
        "hi": "वॉल्यूम बढ़ा दिया सर।"
    },
    "volume_down": {
        "en": "Volume decreased, sir.",
        "te": "వాల్యూమ్ తగ్గించాను సార్.",
        "hi": "वॉल्यूम कम कर दिया सर।"
    },
    "confirm": {
        "en": "Are you sure, sir?",
        "te": "మీకు ఖచ్చితంగా కావాలా సార్?",
        "hi": "क्या आप निश्चित हैं सर?"
    },
    "cancel": {
        "en": "Cancelled, sir.",
        "te": "రద్దు చేశాను సార్.",
        "hi": "रद्द कर दिया सर।"
    },
    "ask_language": {
        "en": "In which programming language should I write this code, sir?",
        "te": "ఈ కోడ్ ఏ ప్రోగ్రామింగ్ భాషలో వ్రాయాలి సార్?",
        "hi": "यह कोड किस प्रोग्रामिंग भाषा में लिखा जाना चाहिए सर?"
    },
    "creator": {
        "en": "I was created by Chaitanya, sir.",
        "te": "నన్ను చైతన్య సృష్టించారు సార్.",
        "hi": "मुझे चैतन्य ने बनाया है सर।"
    },
    "identity": {
        "en": "I am Friday, an advanced male artificial intelligence voice assistant, sir.",
        "te": "నేను ఫ్రైడే, ఒక అడ్వాన్స్‌డ్ పురుష ఆర్టిఫిషియల్ ఇంటెలిజెన్స్ వాయిస్ అసిస్టెంట్‌ని సార్.",
        "hi": "मैं फ्राइडे हूँ, एक उन्नत पुरुष आर्टिफिशियल इंटेलिजेंस वॉयस असिस्टेंट सर।"
    }
}

def msg(key, lang, **kw):
    return MESSAGES[key].get(lang, MESSAGES[key]["en"]).format(**kw)

# ================== MAIN ENGINE ==================

from utils.constants import YES_WORDS, NO_WORDS, is_stop_command, is_cancel_command
# ================== SYSTEM COMMAND KEYWORDS ==================
WIFI_ON_WORDS = (
    "wifi on",
    "వైఫై ఆన్",
    "వైఫై ఆన్ చేయి",
    "वाईफाई चालू",
    "वाईफाई ऑन"
)

WIFI_OFF_WORDS = (
    "wifi off",
    "వైఫై ఆఫ్",
    "వైఫై ఆఫ్ చేయి",
    "वाईफाई बंद",
    "वाईफाई ऑफ"
)

BLUETOOTH_WORDS = (
    "bluetooth",
    "బ్లూటూత్",
    "ब्लूटूथ"
)

HOTSPOT_WORDS = (
    "hotspot",
    "హాట్‌స్పాట్",
    "हॉटस्पॉट"
)

VOLUME_WORDS = (
    "volume", "వాల్యూమ్", "ఆవాజ్", "వాల్యూమ్",
    "आवाज़", "वॉल्यूम", "ध्वनि", "तेज़", "कम"
)

def offline_response(query, lang="en"):
    global PENDING_CONFIRM, PENDING_CODE_DATA
    q = query.lower().strip()
    now = datetime.datetime.now()

    if is_stop_command(q):
        stop_speaking()
        PENDING_CONFIRM = None
        PENDING_CODE_DATA = None
        return True

    if is_cancel_command(q):
        stop_speaking()
        PENDING_CONFIRM = None
        PENDING_CODE_DATA = None
        speak(msg("cancel", lang), lang)
        return True

    # ----- CONFIRMATION -----
    if PENDING_CONFIRM:
        if any(word in q for word in YES_WORDS):
            action = PENDING_CONFIRM
            PENDING_CONFIRM = None
            action()
            return True

        if any(word in q for word in NO_WORDS) or is_cancel_command(q) or is_stop_command(q):
            speak(msg("cancel", lang), lang)
            PENDING_CONFIRM = None
            return True

        # ⛔ Ignore everything else while waiting for yes/no
        return True

    # ----- CODE LANGUAGE CAPTURE -----
    if PENDING_CODE_DATA:
        # Check if user wants to cancel the code request
        if is_cancel_command(q) or is_stop_command(q) or any(w in q for w in NO_WORDS):
            PENDING_CODE_DATA = None
            speak(msg("cancel", lang), lang)
            return True
        # 1. Normalize Language Name
        language_raw = q.strip().lower()
        lang_map = {
            "పైథాన్": "python", "python": "python",
            "జావా": "java", "java": "java",
            "సి ప్లస్ ప్లస్": "cpp", "c plus plus": "cpp", "c++": "cpp",
            "సి": "c", "c": "c",
            "పిహెచ్ పి": "php", "php": "php",
            "జావా స్క్రిప్ట్": "javascript", "javascript": "javascript", "js": "javascript",
            "హెచ్టిఎమ్ఎల్": "html", "html": "html"
        }
        
        language = lang_map.get(language_raw, language_raw)
        task = PENDING_CODE_DATA
        PENDING_CODE_DATA = None 
        
        from controllers.code_controller import save_code_as_pdf
        from core.groq_engine import GROQ_API_URL
        from utils.config import GROQ_API_KEY
        import requests
        
        speak(f"Generating {language} code for {task}...", lang)
        
        # 2. Strict Direct Groq Call — bypasses tool system prompt to force raw code output
        code_prompt = f"Write complete, working {language} code for this task: {task}. Return ONLY the code inside a single markdown code block. No explanations, no comments outside the code."
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": f"You are a code generator. Output ONLY the {language} code inside a single ```{language} ... ``` block. No prose, no explanations outside the code block."},
                    {"role": "user", "content": code_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 1500
            },
            timeout=20
        )
        
        code_result = None
        if response.status_code == 200:
            code_result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        else:
            print(f"Code Gen API Error: {response.status_code} - {response.text}")
        
        if code_result:
            # save_code_as_pdf handles extraction of code from markdown blocks
            final_msg = save_code_as_pdf(code_result, language=language, task=task)
            speak(final_msg, lang)
        else:
            speak("Sorry, I could not generate the code.", lang)
            
        return True


    # ----- IDENTITY / CREATOR -----
    creator_keywords = ["who invented you", "who discovered you", "who created you", "who made you", "నిన్ను ఎవరు కనిపెట్టారు", "నిన్ను ఎవరు సృష్టించారు", "तुम्हें किसने बनाया", "तुम्हें किसने खोजा"]
    if any(word in q for word in creator_keywords):
        speak(msg("creator", lang), lang)
        return True

    identity_keywords = ["who are you", "what are you", "what is your name", "నీవు ఎవరివి", "నువ్వు ఎవరు", "నీ పేరు ఏమిటి", "तुम कौन हो", "आप कौन हैं", "तुम्हारा नाम क्या है"]
    if any(word in q for word in identity_keywords) and "how are you" not in q:
        speak(msg("identity", lang), lang)
        return True

    # ----- TIME / DATE / DAY -----
    if any(word in q for word in ["time", "సమయం", "समय", "టైమ్", "టైం"]):
        speak(msg("time", lang, value=now.strftime("%I:%M %p")), lang)
        return True

    if "date" in q or "తేదీ" in q or "तारीख" in q:
        speak(msg("date", lang, value=now.strftime("%d %B %Y")), lang)
        return True

    if any(word in q for word in ["what day", "ఏ వారం", "कौन सा दिन"]) and "weather" not in q and "వాతావరణం" not in q:
        speak(msg("day", lang, value=now.strftime("%A")), lang)
        return True

    # ----- ALARM SETTING -----
    alarm_time_str = None
    from controllers.alarm_controller import parse_time, set_windows_alarm

    TELUGU_NUMS = {
        "సున్న": "0", "ఒకటి": "1", "రెండు": "2", "మూడు": "3",
        "నాలుగు": "4", "అయిదు": "5", "ఆరు": "6", "ఏడు": "7",
        "ఎనిమిది": "8", "తొమ్మిది": "9", "పది": "10", "పదకొండు": "11",
        "పన్నెండు": "12"
    }
    HINDI_NUMS = {
        "शून्य": "0", "एक": "1", "दो": "2", "तीन": "3", "चार": "4",
        "पाँच": "5", "छह": "6", "सात": "7", "आठ": "8", "नौ": "9",
        "दस": "10", "ग्यारह": "11", "बारह": "12"
    }

    def normalize_to_digits(text, num_map):
        for word, digit in num_map.items():
            text = text.replace(word, digit)
        return text

    alarm_keywords = [
        "alarm", "wake me up", "wake me",
        "అలారం", "నన్ను లేపు", "లేపు", "నిద్ర లేపు",
        "अलार्म", "उठाओ", "जगाओ"
    ]

    if any(k in q for k in alarm_keywords):
        norm_q = q
        if lang == "te":
            norm_q = normalize_to_digits(q, TELUGU_NUMS)
        elif lang == "hi":
            norm_q = normalize_to_digits(q, HINDI_NUMS)
            
        h, m, ap = parse_time(norm_q)
        if h:
            alarm_time_str = f"{h}:{m} {ap}"

    if alarm_time_str:
        setting_msg = {
            "en": f"Setting an alarm for {alarm_time_str}.",
            "te": f"{alarm_time_str} కి అలారం సెట్ చేస్తున్నాను.",
            "hi": f"{alarm_time_str} के लिए अलार्म सेट कर रहा हूँ।"
        }
        speak(setting_msg.get(lang, setting_msg["en"]), lang)
        result_msg = set_windows_alarm(alarm_time_str)
        # Translate result message if needed
        done_msg = {
            "en": result_msg,
            "te": f"అలారం సెట్ అయింది: {alarm_time_str}",
            "hi": f"अलार्म सेट हो गया: {alarm_time_str}"
        }
        speak(done_msg.get(lang, result_msg), lang)
        return True

    # ----- SCREENSHOT -----
    if "screenshot" in q or "స్క్రీన్" in q or "स्क्रीनशॉट" in q:
        img = ImageGrab.grab()
        img.save(f"screenshot_{now.strftime('%H%M%S')}.png")
        speak(msg("screenshot", lang), lang)
        return True


    # ----- OPEN WEBSITE -----
    website_keywords = ["website", "వెబ్‌సైట్", "వెబ్ సైట్", "వెబ్సైట్", "वेबसाइट", "वेब साईट", "वेब साइट"]
    if q.startswith(("open ", "ఓపెన్ ", "खोलो ")) and any(w in q for w in website_keywords):
        from controllers.browser_controller import open_website
        if open_website(q.split(" ", 1)[1]):
            speak(msg("open_app", lang, app=q.split(" ", 1)[1]), lang)
            return True

    # ----- OPEN APP -----
    if q.startswith(("open ", "ఓపెన్ ", "खोलो ")):
        return open_app(q.split(" ", 1)[1], lang, msg)

    # ----- CLOSE WEBSITE -----
    if q.startswith(("close ", "క్లోజ్ ", "बंद ")) and any(w in q for w in website_keywords):
        from controllers.browser_controller import close_website
        
        # Extract the website name from the query
        website_to_close = q
        prefixes = ["close ", "క్లోజ్ ", "बंद "]
        for prefix in prefixes:
            if website_to_close.startswith(prefix):
                website_to_close = website_to_close[len(prefix):].strip()
                break
        
        # Remove website keywords
        for w in website_keywords:
            if website_to_close.endswith(w):
                website_to_close = website_to_close[:-len(w)].strip()
                break
        
        PENDING_CONFIRM = lambda: speak(close_website(website_to_close), lang)
        speak(msg("confirm", lang), lang)
        return True

    # ----- CLOSE APP -----
    if q.startswith(("close ", "క్లోజ్ ", "बंद ")):
        app = q.split(" ", 1)[1]
        PENDING_CONFIRM = lambda: close_app(app, lang, msg)
        speak(msg("confirm", lang), lang)
        return True

    # ----- WIFI -----
    if any(word in q for word in WIFI_ON_WORDS):
        wifi(True)
        speak(msg("wifi_on", lang), lang)
        return True

    if any(word in q for word in WIFI_OFF_WORDS):
        PENDING_CONFIRM = lambda: wifi(False)
        speak(msg("confirm", lang), lang)
        return True

    # ----- BLUETOOTH / HOTSPOT -----
    if any(word in q for word in BLUETOOTH_WORDS):
        bluetooth()
        speak(msg("bluetooth", lang), lang)
        return True

    if any(word in q for word in HOTSPOT_WORDS):
        hotspot()
        speak(msg("hotspot", lang), lang)
        return True

    # ----- VOLUME -----
    match = re.search(r'(\d+)\s*(percent|%)', q)
    if "volume" in q and match:
        p = int(match.group(1))
        set_volume(p)
        speak(msg("volume_set", lang, value=p), lang)
        return True

    if "increase volume" in q or "వాల్యూమ్ పెంచు" in q or "आवाज़ बढ़ाओ" in q:
        volume_up()
        speak(msg("volume_up", lang), lang)
        return True

    if "decrease volume" in q or "వాల్యూమ్ తగ్గించు" in q or "आवाज़ कम करो" in q:
        volume_down()
        speak(msg("volume_down", lang), lang)
        return True

    return False
