# constants.py

# ================== LANGUAGE KEYWORDS ==================
YES_WORDS = (
    "yes", "yeah", "yep", "sure", "ok", "okay",
    "అవును", "సరే",
    "हाँ", "ठीक", "ठीक है"
)

NO_WORDS = (
    "no", "nope",
    "కాదు",
    "नहीं"
)

# ================== STOP WORDS ==================
STOP_WORDS = [
    # English - natural stop phrases and words
    "stop",
    "stop it",
    "stop now",
    "stop please",
    "please stop",
    "just stop",
    "okay stop",
    "friday stop",
    "stop friday",
    "stop speaking",
    "stop talking",
    "that's enough",
    "thats enough",
    "enough now",
    "shut up",
    "be quiet",
    "quiet please",
    "hush",
    "halt",
    "pause",
    "hold on",

    # Telugu
    "ఆపు",
    "ఆపండి",
    "చాలు",
    "ఆపు ఆపు",
    "మాట్లాడటం ఆపు",
    "చాలు ఆపు",
    "రుకో",

    # Hindi
    "रुको",
    "रुको रुको",
    "रुक जाओ",
    "बस",
    "बस करो",
    "बस बस",
    "चुप",
    "चुप रहो",
    "बोलना बंद करो",
    "बंद करो",
    "रोक दो",
]

# ================== CANCEL WORDS ==================
# These trigger a soft "cancel + re-listen" rather than hard stop
CANCEL_WORDS = [
    "sorry",
    "cancel",
    "cancel that",
    "cancel it",
    "my mistake",
    "that's wrong",
    "ignore that",
    "forget it",
    "never mind",
    "nevermind",
    "abort",
    "dismiss",
    "no need",

    # Telugu
    "క్షమించండి",
    "తప్పు",
    "క్యాన్సల్",
    "వద్దు",
    "రద్దు",
    "వదిలేయ్",

    # Hindi
    "माफ करना",
    "गलती",
    "कैंसिल",
    "छोड़ो",
    "रद्द करो",
    "रहने दो",
]

EXIT_WORDS = [
    "friday exit",
    "go to sleep",
    "goodbye friday",
    "good night friday",
    "sleep now",
    "exit",
    "bye friday",
    "goodbye",
    "close friday",

    # Telugu
    "వెళ్ళు",
    "నిద్ర",
    "గుడ్ నైట్",
    "ముగించు",

    # Hindi
    "सो जाओ",
    "गुड नाइट",
    "बंद हो जाओ",
]

# ================== INTENT PREDICATES ==================
QUESTION_STARTERS = {
    "what", "why", "how", "who", "where", "when", "which", "tell", "explain",
    "search", "google", "is", "are", "can", "could", "do", "does",
    "ఏమిటి", "ఎందుకు", "ఎలా", "ఎవరు", "ఎక్కడ", "ఎప్పుడు",
    "क्या", "क्यों", "कैसे", "कौन", "कहाँ", "कब"
}

def is_stop_command(text: str) -> bool:
    """Detects if an utterance is an intentional Hard Stop command."""
    if not text:
        return False
    t = text.lower().strip().rstrip('.!?')
    # Exact match
    if any(phrase == t for phrase in STOP_WORDS):
        return True
    # If starting with a question word, it's a general query (e.g. 'what is bus stop')
    words = t.split()
    if words and words[0] in QUESTION_STARTERS:
        return False
    # Short commands starting or ending with a stop phrase
    if any(t.startswith(phrase + " ") or t.endswith(" " + phrase) for phrase in STOP_WORDS):
        return True
    return False

def is_cancel_command(text: str) -> bool:
    """Detects if an utterance is an intentional Soft Cancel command."""
    if not text:
        return False
    t = text.lower().strip().rstrip('.!?')
    # Exact match
    if any(phrase == t for phrase in CANCEL_WORDS):
        return True
    words = t.split()
    if words and words[0] in QUESTION_STARTERS:
        return False
    if any(t.startswith(phrase + " ") or t.endswith(" " + phrase) for phrase in CANCEL_WORDS):
        return True
    return False

def is_exit_command(text: str) -> bool:
    """Detects if an utterance is an exit/sleep command."""
    if not text:
        return False
    t = text.lower().strip().rstrip('.!?')
    if any(phrase == t for phrase in EXIT_WORDS):
        return True
    if any(t.startswith(phrase + " ") or t.endswith(" " + phrase) for phrase in EXIT_WORDS):
        return True
    return False

# ================== VOICE FILTER PROMPTS ==================
# Fragments of Friday's own voice output — used to filter mic echo/self-hearing
FRIDAY_PROMPTS = [
    "please say the secret code",
    "please choose language",
    "english telugu or hindi",
    "friday is running",
    "i am ready",
    "you can speak now",
    "i didn't catch that",
    "try again",
    "attempts left",
    "wrong code",
    "access denied",
    "going back to sleep",
    "got it", "listening again",
    "could not close", "website tab",
    "closing the active",
    "opening whatsapp",
    "access granted",
    "i am friday",
    "how can i help",
    "hello chaitanya",

    # Telugu
    "భాషను ఎంచుకోండి", "తెలుగు ఎంచుకోబడింది", "నేను సిద్ధంగా ఉన్నాను",
    "మీరు ఇప్పుడు మాట్లాడవచ్చు", "రహస్య కోడ్", "మళ్ళీ ప్రయత్నించండి",
    "నిద్రపోతున్నాను", "అనుమతి నిరాకరించబడింది",
    "సరే", "మళ్ళీ వింటున్నాను", "క్లోజ్ చేయలేకపోయాను",

    # Hindi
    "भाषा चुनें", "हिंदी चुनी गई", "मैं तैयार हूँ",
    "आप अभी बोल सकते हैं", "गुप्त कोड", "फिर से प्रयास करें",
    "सो रहा हूँ", "पहुँच अस्वीकार",
    "ठीक है", "फिर से सुन रहा हूँ", "बंद नहीं कर सका"
]
