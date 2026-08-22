from core.offline_engine import offline_response
from core.groq_engine import qwen_response
from services.translator import to_english, from_english
from services.tts import speak
from controllers.productivity_controller import get_system_status, read_clipboard
from controllers.code_controller import save_code_as_pdf
from controllers.vision_controller import capture_and_describe
from controllers.whatsapp_controller import send_whatsapp_message, make_whatsapp_call, reject_call
from controllers.browser_controller import open_website, close_website, search_query
from controllers.weather_controller import get_weather
from controllers.news_controller import get_news
from controllers.currency_controller import convert_currency
from controllers.map_controller import open_map
import re

# ------------------ HELPERS ------------------

from utils.constants import YES_WORDS, NO_WORDS

APP_KEYWORDS = (
    "open", "close", "start",
    "ఓపెన్", "క్లోజ్",
    "खोलो", "बंद"
)

# ------------------ FAST RESPONSES (0ms Latency) ------------------
FAST_RESPONSES = {
    "hi": "Hello! How can I help you today?",
    "hello": "Hello! How can I help you today?",
    "how are you": "I am doing great! Ready to assist you. What can I do for you?",
    "what can you do": "I can help you with searches, weather, reminders, system stats, code, and more! Just ask.",
    "thank you": "You're very welcome!",
    "thanks": "You're very welcome!",
    "bye": "Goodbye! Have a great day!",
    "goodbye": "Goodbye! Have a great day!"
}

# ------------------ MAIN HANDLER ------------------

def handle_query(query, lang):
    query_l = query.lower().strip()

    # 1️⃣ FAST RESPONSE LAYER (Local check)
    if query_l in FAST_RESPONSES:
        answer = FAST_RESPONSES[query_l]
        if lang in ("te", "hi"):
            answer = from_english(answer, lang)
        speak(answer, lang)
        return

    # 2️⃣ OFFLINE ENGINE (Local system commands: time, date, volume, etc.)
    # High priority to prevent search shadowing
    handled = offline_response(query, lang)
    if handled:
        return

    # 3️⃣ NO TRANSLATION NEEDED - Pass directly to Groq natively!
    english_query = query # Keep original variable name to avoid refactoring impact

    # 3️⃣ ASK LLM (Agentic Response)
    # the LLM will generate native text (e.g. native Telugu) but with English tool formatting
    english_answer = qwen_response(english_query, lang=lang)

    if not english_answer:
        speak("Sorry, I could not find an answer.", lang)
        return

    # 4️⃣ AGENTIC TOOL HANDLING
    
    # --- AUTO-DETECT AND SILENCE CODE BLOCKS ---
    if "```" in english_answer:
        # 1. Pre-emptive Intercept: If language wasn't chosen yet, force the tool flow
        from core import offline_engine
        if not offline_engine.PENDING_CODE_DATA:
            # AI tried to give code without being asked for language. Stop it.
            offline_engine.PENDING_CODE_DATA = query # The original request
            from core.offline_engine import msg
            speak(msg("ask_language", lang), lang)
            return

        # 2. Extract all blocks with robust regex
        regex = r'```(?:\w+)?\s*\n?(.*?)\n?```'
        blocks = re.findall(regex, english_answer, re.DOTALL)
        if blocks:
            # 2. Get language
            lang_match = re.search(r'```(\w+)', english_answer)
            code_lang = lang_match.group(1) if lang_match else "python"
            
            # 3. Save to PDF
            from controllers.code_controller import save_code_as_pdf
            pdf_msg = save_code_as_pdf(blocks[0], language=code_lang)
            
            # 4. Create a clean spoken confirmation
            # Remove the code blocks and the [CODE] tag if present
            clean_msg = re.sub(regex, "", english_answer, flags=re.DOTALL)
            clean_msg = clean_msg.replace("[CODE]", "").strip()
            # Remove double newlines/extra whitespace for cleaner speech
            clean_msg = re.sub(r'\n+', ' ', clean_msg)
            # Extra safety: remove any dangling [CODE] or tools
            for tool in ["[VISION]", "[SEARCH]", "[REMINDER]", "[SYSTEM]", "[WHATSAPP]"]:
                clean_msg = clean_msg.replace(tool, "")
            
            clean_msg = clean_msg.strip()
            
            # Combine original text (if any) with the PDF success message
            final_text = f"{clean_msg} {pdf_msg}".strip()
            
            # 5. NO TRANSLATION NEEDED (Text is already perfectly native from Groq!)
            speak(final_text, lang)
            return # EXIT EARLY - Code is handled
    
    final_output = english_answer # Continue for other tools
    
    # 4. TOOL HANDLING
    clean_answer = english_answer.split("\n")[0].strip() # Look at the first line for the tool tag

    if "[VISION]" in clean_answer:
        final_output = capture_and_describe()

    elif "[SEARCH]" in clean_answer:
        q = clean_answer.split("[SEARCH]", 1)[1].strip()
        final_output = search_query(q)
        
    elif "[WEATHER]" in clean_answer:
        city = clean_answer.split("[WEATHER]", 1)[1].strip()
        final_output = get_weather(city)

    elif "[NEWS]" in clean_answer:
        category = clean_answer.split("[NEWS]", 1)[1].strip()
        if not category: category = "general"
        final_output = get_news(category)

    elif "[MAPS]" in clean_answer:
        location = clean_answer.split("[MAPS]", 1)[1].strip()
        final_output = open_map(location)

    elif "[CURRENCY]" in clean_answer:
        q = clean_answer.split("[CURRENCY]", 1)[1].strip()
        final_output = convert_currency(q)
            
    elif "[REMINDER]" in clean_answer:
        final_output = "The reminder feature has been disabled."

    elif "[WHATSAPP_CHAT]" in clean_answer:
        # Extract everything after the tag on the SAME line
        tools_data = clean_answer.split("[WHATSAPP_CHAT]", 1)[1].strip()
        parts = tools_data.split("|")
        if len(parts) >= 2:
            final_output = send_whatsapp_message(parts[0].strip(), parts[1].strip())
        else:
            final_output = "I need both a contact name and a message to send a WhatsApp."
            
    elif "[WHATSAPP_CALL]" in clean_answer:
        name = clean_answer.split("[WHATSAPP_CALL]", 1)[1].strip()
        final_output = make_whatsapp_call(name, video=False)

    elif "[WHATSAPP_VIDEO]" in clean_answer:
        name = clean_answer.split("[WHATSAPP_VIDEO]", 1)[1].strip()
        final_output = make_whatsapp_call(name, video=True)

    elif "[WHATSAPP_REJECT]" in clean_answer:
        final_output = reject_call()
            
    elif "[WHATSAPP_ADD]" in clean_answer:
        tools_data = clean_answer.split("[WHATSAPP_ADD]", 1)[1].strip()
        parts = tools_data.split("|")
        if len(parts) >= 2:
            from controllers.whatsapp_controller import add_contact_to_db
            final_output = add_contact_to_db(parts[0].strip(), parts[1].strip())
        else:
            final_output = "I need both a contact name and a phone number to save a contact."
            
    elif "[SYSTEM]" in clean_answer:
        final_output = get_system_status()
        
    elif "[CODE]" in english_answer:
        code_task = english_answer.split("[CODE]", 1)[1].strip()
        from core import offline_engine
        offline_engine.PENDING_CODE_DATA = code_task
        from core.offline_engine import msg
        speak(msg("ask_language", lang), lang)
        return

    elif "clipboard" in english_answer.lower():
        final_output = read_clipboard()

    # 5️⃣ TRANSLATE TOOL TEXT IF NEEDED 
    # If final_output matches english_answer, it means no tool intercepted it and it is pure Groq Native speech. 
    # Do NOT translate it (because Groq already perfectly translated it!).
    # If it does NOT match, it means a local Python tool sent back English text (e.g. "The weather is..."), so we MUST translate it.
    if lang in ("te", "hi") and final_output != english_answer:
        final_answer = from_english(final_output, lang)
    else:
        final_answer = final_output

    speak(final_answer, lang)
