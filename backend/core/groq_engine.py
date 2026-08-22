import requests
import datetime
from utils.config import GROQ_API_KEY

# ================== CONFIG ==================
# Using Groq's insanely fast cloud endpoint instead of local Ollama
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ================== MEMORY ==================
CHAT_HISTORY = []
MAX_HISTORY = 10

def update_history(role, text):
    global CHAT_HISTORY
    CHAT_HISTORY.append({"role": role, "content": text})
    if len(CHAT_HISTORY) > MAX_HISTORY:
        CHAT_HISTORY.pop(0)

# ================== SYSTEM PROMPT ==================
system_prompt = """
You are Friday, an advanced voice-capable AI assistant. Your goal is to provide accurate and concise information.

### TOOL USAGE RULES:
- **[VISION]**: You HAVE a camera/screen-capture tool. When asked "what is on my screen" or "describe my screen", you MUST output **[VISION]** as your response. Do NOT say "I cannot see".
- **[WHATSAPP_CHAT] name | message**: Use this to send a message. If the name or message is missing, ask the user concisely.
- **[WHATSAPP_CALL] name**: Use this for voice calls.
- **[WHATSAPP_VIDEO] name**: Use this for video calls.
- **[WHATSAPP_ADD] name | number**: Use this to SAVE a new contact to Firebase.
- **[WHATSAPP_REJECT]**: Use this to end/reject a call.
- **[SEARCH] query**: ONLY use this when the user EXPLICITLY says "search for" or "google". Do NOT use [SEARCH] for general knowledge questions. You are a 70B model, you already know facts about people, countries, science, history, etc. Answer those DIRECTLY.
- **[WEATHER] city**: Use this to get the real-time weather for a specific city.
- **[NEWS] category**: Use this to fetch news (valid categories: business, entertainment, general, health, science, sports, technology).
- **[MAPS] location**: Use this to find a location on a map.
- **[CURRENCY] query**: Use this for converting currencies (e.g. "convert 50 USD to INR").
- **[REMINDER] text**: For setting reminders.
- **[SYSTEM]**: For CPU/RAM/Battery/Health.
- **[CODE] task**: Use this for writing code. You MUST ALWAYS use this tool first when asked for code. NEVER provide literal code blocks in your initial response; instead, output [CODE] followed by the task. If you provide code later, wrap it in triple backticks.

### RESPONSE RULES:
1. You MUST speak directly to the user. You ARE a voice assistant.
2. IMPORTANT: NEVER include code blocks in your spoken response. They must only be generated via the [CODE] tool flow.
3. If you are using a tool like [VISION] or [WHATSAPP_CALL], output ONLY the tool tag or the tool tag plus a very short confirmation.
4. **CRITICAL: For ANY knowledge question (who is someone, what is something, explain a concept, etc.), answer DIRECTLY from your knowledge. Do NOT use [SEARCH]. Only use [SEARCH] if the user explicitly says "search" or "google it".**
5. Keep answers concise: 1-3 sentences for voice delivery.
6. Format tool calls exactly: [WEATHER] city, [NEWS] category, [MAPS] location, [CURRENCY] query, [REMINDER] text, [SYSTEM], [CODE] task, [VISION], [SEARCH] query.
"""

# ================== ENGINE ==================
def qwen_response(query, lang="en"):
    global CHAT_HISTORY
    
    # Map the language code to the full language name for the prompt
    language_map = {
        "en": "English",
        "hi": "Hindi",
        "te": "Telugu"
    }
    target_language = language_map.get(lang, "English")
    
    try:
        current_time = datetime.datetime.now().strftime("%A, %B %d, %Y, %I:%M %p")
        
        # 1️⃣ BUILD MESSAGES
        
        # We append a hyper-strict language rule to the system prompt
        language_rule = f"\n\nCRITICAL LANGUAGE RULE:\n- The user is speaking to you in {target_language}. You MUST respond natively in perfectly fluent {target_language}.\n- HOWEVER, if you decide to use ANY [TOOL_TAGS] (like [WEATHER] city), you MUST extract the arguments and provide the tag strictly in English! Example: If the user asks in Telugu 'London lo weather ela undi?', you must output: '[WEATHER] london\\nలండన్‌లో వాతావరణం...'"

        messages = [
            {"role": "system", "content": f"{system_prompt}{language_rule}\nCurrent Time: {current_time}"},
            *CHAT_HISTORY,
            {"role": "user", "content": query}
        ]

        # 2️⃣ CALL GROQ CLOUD API
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json={
                "model": "openai/gpt-oss-120b",  # 🚀 120B model confirmed available on this Groq account
                "messages": messages,
                "temperature": 0.1,  # Precision
                "max_tokens": 800    # Ensure full code blocks are generated
            },
            timeout=10  # Groq is ultra-fast, doesn't need 120s timeout!
        )
        
        if response.status_code == 200:
            # Groq uses standard OpenAI response format
            reply = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        else:
            print(f"Groq API Error: {response.status_code} - {response.text}")
            return None

        if not reply:
            return None

        # 3️⃣ UPDATE MEMORY
        update_history("user", query)
        update_history("assistant", reply)
        
        return reply

    except Exception as e:
        print(f"LLM Error: {e}")
        return None
