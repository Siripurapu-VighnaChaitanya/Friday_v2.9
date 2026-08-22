# Friday v2.9 — Advanced 3D AI Voice Assistant

Friday v2.9 is a modern, voice-operated desktop AI assistant featuring a real-time procedural 3D holographic avatar, 2D particle engine, multi-language speech support (English, Telugu, Hindi), system automation, and agentic tool integrations.

---

## 🌟 Key Features

- **3D Holographic Avatar Engine**: Built on Three.js with real-time procedural lip-sync, dynamic lighting, emotion presets, and state animations.
- **2D Particle Sphere Widget**: Integrated audio-responsive canvas orb with state transitions.
- **Multilingual Support**: Real-time voice interaction in English, Telugu (`te-IN`), and Hindi (`hi-IN`).
- **High-Speed Cloud LLM Integration**: Powered by Groq ultra-fast 120B parameter model.
- **Offline System Controllers**:
  - Alarms & Clock integration (Windows Clock automation with NLP time parsing).
  - App launcher and system controllers (Volume, WiFi, Bluetooth, Hotspot).
  - Web browsing, currency conversion, maps, weather, and news.
  - Code generator that exports cleanly formatted syntax PDFs directly to Desktop.
- **Real-Time Terminal Session Log**: Hacker-themed HUD stream showing live queries, responses, and timestamps.
- **Instant Interrupt Controls**: Hard Stop (*"stop"*, *"shut up"*, *"ఆపు"*, *"रुको"*) and Soft Cancel (*"cancel"*, *"sorry"*, *"వద్దు"*, *"छोड़ो"*).

---

## 📁 Repository Structure

```text
Friday_v2.9/
├── assets/
│   ├── facecap.bin              # 3D Mesh & Blendshape Model
│   └── friday_logo.png          # App Branding
├── backend/
│   ├── controllers/             # System, Alarm, App, Vision, Code controllers
│   ├── core/                    # Speech Listener, Groq Engine, Mode Manager, Offline Engine
│   ├── services/                # TTS, WebSocket UI Server, Language Manager
│   ├── utils/                   # Config, Constants, Firebase helpers
│   ├── main.py                  # Backend orchestrator & PyWebview host
│   ├── requirements.txt         # Python dependencies
│   └── friday_commands.html     # Interactive Command Guide
└── frontend/
    ├── 2d_widget/               # 2D Particle Sphere Canvas Widget
    └── 3d_avatar/               # Three.js 3D Holographic Avatar UI & Controls
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+
- Microsoft Edge WebView2 (pre-installed on Windows 10/11)

### 2. Setup Virtual Environment
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure API Keys
Copy `.env.example` to `.env` and fill in your keys:
```env
GROQ_API_KEY=your_groq_api_key_here
WEATHER_API_KEY=your_openweather_api_key_here
NEWS_API_KEY=your_news_api_key_here
EXCHANGE_RATE_KEY=your_exchangerate_api_key_here
FIREBASE_CREDENTIALS_PATH=friday-4069f-firebase-adminsdk-fbsvc-2df7994540.json
```

### 4. Run Friday
```powershell
python main.py
```
Say **"Hello Friday"** or your wake word to start interacting!
