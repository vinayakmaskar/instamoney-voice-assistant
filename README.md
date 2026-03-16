# InstaMoney — Voice-Powered Loan Application Assistant

> **Gemini Live Agent Challenge** | Category: **Live Agents**

InstaMoney is a real-time, multilingual voice assistant that helps users fill out loan application forms through natural speech. Instead of typing into a traditional form, users simply talk — the assistant listens, understands, and auto-fills the form fields in real time.

Built with the **Google Gemini Live API** for streaming bi-directional audio, **Django Channels** for WebSocket communication, and a **React Native (Expo)** frontend with a modern glassmorphism UI.

### Live Demo

**Try it now:** [https://voice-chatbot-backend-7uucccu35q-el.a.run.app](https://voice-chatbot-backend-7uucccu35q-el.a.run.app)

Hosted on **Google Cloud Run** (Mumbai region). Click the microphone button and start speaking.

---

## Features

### Core Capabilities
- **Real-time voice interaction** — Speak naturally, the assistant fills your form
- **Streaming audio** — Bi-directional audio via Gemini Live API (no record-and-send; truly live)
- **Auto-fill from speech** — AI extracts field values (name, PAN, DOB, state, language) and fills the form instantly
- **Multilingual support** — 10 Indian languages: English, Hindi, Marathi, Tamil, Telugu, Bengali, Gujarati, Kannada, Malayalam, Punjabi
- **Dynamic language switching** — Switch languages mid-conversation; the bot follows immediately
- **Voice Activity Detection (VAD)** — Frontend-side silence detection for responsive turn-taking

### User Experience
- **Glassmorphism UI** — Modern dark-themed interface with gradient accents, animated progress, and floating labels
- **Live form updates** — Fields light up green with checkmarks as the bot fills them
- **Animated voice button** — Pulsing FAB with ripple effects, waveform bars during recording, and status cards
- **Field-fill notifications** — Brief toast-style notification when each field is auto-filled
- **Error resilience** — Auto-reconnection to Gemini Live API with up to 3 retries

### Technical Highlights
- **Zero-latency audio pipeline** — PCM 16-bit 24kHz mono audio streamed directly over WebSocket (no base64, no encoding overhead)
- **Subprotocol JWT auth** — Token passed as WebSocket subprotocol for secure, stateless authentication
- **Tool calling** — Gemini uses `fill_form_field` function calls to structured-fill form fields with confidence scores
- **Continuous response receiver** — Background asyncio task continuously reads from the Gemini Live session
- **Transcript accumulation** — User and bot speech transcripts stored in the database for audit

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER (Browser)                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  React Native (Expo Web)                                     │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │   │
│  │  │ Microphone   │  │ Voice Button │  │ BasicDetailsForm   │  │   │
│  │  │ (Web Audio)  │  │ (FAB + Anim) │  │ (Auto-fill fields) │  │   │
│  │  └──────┬───────┘  └──────────────┘  └────────▲───────────┘  │   │
│  │         │ PCM 16-bit 24kHz mono               │ form_update   │   │
│  │         ▼                                     │               │   │
│  │  ┌──────────────────────────────────────────────────────────┐ │   │
│  │  │           WebSocket Client (subprotocol JWT)             │ │   │
│  │  └──────────────────────┬───────────────────────────────────┘ │   │
│  └─────────────────────────┼────────────────────────────────────┘   │
└────────────────────────────┼────────────────────────────────────────┘
                             │ ws://  (binary audio ↕ JSON messages)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BACKEND (Django + Daphne)                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Django Channels — VoiceChatbotConsumer (ASGI WebSocket)     │   │
│  │  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐  │   │
│  │  │ JWT Auth     │  │ Audio Router  │  │ Tool Call Handler │  │   │
│  │  │ (security.py)│  │ (binary→API)  │  │ (fill_form_field) │  │   │
│  │  └──────────────┘  └───────┬───────┘  └──────────────────┘  │   │
│  └────────────────────────────┼─────────────────────────────────┘   │
│                               │                                     │
│  ┌────────────────────────────▼─────────────────────────────────┐   │
│  │  LoanAssistantAgent (services/adk_agent.py)                  │   │
│  │  ┌──────────────────────────────────────────────────────┐    │   │
│  │  │  Google GenAI SDK  →  Gemini Live API                │    │   │
│  │  │  • System prompt with form field definitions         │    │   │
│  │  │  • fill_form_field tool declaration                  │    │   │
│  │  │  • Streaming audio in/out (bidiGenerateContent)      │    │   │
│  │  │  • Transcript extraction (input + output)            │    │   │
│  │  └──────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────────┐ │
│  │ SQLite DB   │  │ Django ORM   │  │ Session & Conversation Mgmt│ │
│  └─────────────┘  └──────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GOOGLE CLOUD                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Gemini 2.5 Flash (Native Audio)                             │   │
│  │  • bidiGenerateContent (Live API)                            │   │
│  │  • Real-time speech-to-speech with tool calling              │   │
│  │  • Multilingual audio understanding + generation             │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **AI Model** | Gemini 2.5 Flash Native Audio | Live streaming speech-to-speech with tool calling |
| **AI SDK** | Google GenAI SDK (`google-genai`) | Gemini Live API client (`bidiGenerateContent`) |
| **Backend** | Django 4.2 + Django Channels | ASGI WebSocket server |
| **ASGI Server** | Daphne | Production WebSocket-capable server |
| **Frontend** | React Native (Expo 49) | Cross-platform UI (Web, iOS, Android) |
| **Audio** | Web Audio API | Real-time PCM capture and playback at 24kHz |
| **Auth** | JWT (PyJWT) | Stateless token auth via WebSocket subprotocol |
| **Database** | SQLite (dev) | Session and conversation storage |
| **Styling** | Custom glassmorphism theme | Dark UI with gradient accents |

---

## Project Structure

```
voice_chatbot2/
├── config/                 # App configuration & secrets loader
│   └── settings.py         # Centralized config (Gemini, JWT, audio)
├── consumers/              # Django Channels WebSocket consumers
│   ├── consumers.py        # VoiceChatbotConsumer — main WS handler
│   └── routing.py          # WebSocket URL routing
├── frontend/               # React Native (Expo) frontend
│   ├── App.js              # Root component with form state
│   └── src/
│       ├── components/
│       │   ├── BasicDetailsForm.js   # Form with floating labels, icons
│       │   └── VoiceChatbot.js       # Voice FAB with animations
│       ├── services/
│       │   └── websocket.js          # WebSocket client with subprotocol auth
│       └── styles/
│           └── theme.js              # Glassmorphism design tokens
├── models/                 # Django models
│   └── conversation.py     # Session & message models
├── services/               # Core business logic
│   ├── adk_agent.py        # LoanAssistantAgent — Gemini Live API integration
│   ├── database.py         # Database operations (async)
│   └── security.py         # JWT validation, rate limiting, input sanitization
├── voice_chatbot/          # Django project settings
│   ├── asgi.py             # ASGI config with protocol routing
│   ├── settings.py         # Django settings
│   └── urls.py             # HTTP URL config
├── tests/                  # Test suite
├── manage.py               # Django management
├── requirements.txt        # Python dependencies
├── secrets.json.example    # Template for secrets (copy to secrets.json)
├── Dockerfile              # Production container (Python 3.11 + Daphne)
├── deploy.sh               # Automated GCP Cloud Run deployment script
├── .gcloudignore           # Cloud Build file inclusion overrides
├── .dockerignore           # Docker build exclusions
├── architecture_diagram.html # Interactive system architecture diagram
├── BLOG_POST.md            # Project write-up for hackathon submission
├── quick_start.sh          # One-command server startup
└── start_servers.sh        # Production server startup script
```

---

## Quick Start (Spin-Up Instructions)

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm**
- **Google Cloud account** with Gemini API access

### 1. Clone the repository

```bash
git clone https://github.com/vinayakmaskar/instamoney-voice-assistant.git
cd instamoney-voice-assistant
```

### 2. Backend setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Configure secrets
cp secrets.json.example secrets.json
# Edit secrets.json and add your GEMINI_API_KEY
```

### 3. Database setup

```bash
python manage.py migrate
python manage.py createsuperuser --username testuser --email test@test.com
```

### 4. Generate a JWT token

```bash
python generate_test_token.py
# Copy the token and paste it into frontend/src/components/VoiceChatbot.js (TEST_TOKEN)
```

### 5. Start the backend

```bash
daphne -b 127.0.0.1 -p 8000 voice_chatbot.asgi:application
```

### 6. Frontend setup (new terminal)

```bash
cd frontend
npm install
npx expo start --web --port 8081
```

### 7. Open in browser

Navigate to **http://localhost:8081** and click the microphone button to start talking.

---

## How It Works

### 1. Connection
User clicks the mic button → Frontend opens a WebSocket to the backend with JWT token as subprotocol → Backend validates token, creates a session, and opens a **Gemini Live API** bi-directional streaming session.

### 2. Greeting
The bot automatically sends a greeting: *"Hello! Welcome to InstaMoney. I'm here to help you fill out your Basic Details form. What's your full name?"*

### 3. Voice Interaction
User speaks → Frontend captures audio via Web Audio API as **PCM 16-bit 24kHz mono** → Streams raw binary over WebSocket → Backend forwards to Gemini Live API → Gemini processes speech, generates a response, and optionally calls the `fill_form_field` tool.

### 4. Form Filling
When Gemini detects a form field value in the user's speech, it calls `fill_form_field(field_name, field_value)` → Backend sends a `form_suggestion` message to the frontend → Frontend auto-fills the corresponding field with a green animation.

### 5. Audio Response
Gemini's audio response streams back through the same pipeline → Backend sends raw PCM chunks over WebSocket → Frontend plays them in real-time using Web Audio API with a queue-based system to prevent overlaps.

---

## Google Cloud Services Used

| Service | Usage |
|---------|-------|
| **Gemini Live API** | Core AI — real-time streaming speech-to-speech with function calling |
| **Google GenAI SDK** | Client library for Gemini API access (`google-genai`) |
| **Cloud Run** | Hosts backend (Daphne ASGI) + serves frontend — WebSocket-enabled, auto-scaling |
| **Cloud Build** | Builds Docker images from source on push |
| **Secret Manager** | Stores `secrets.json` (API keys, JWT keys) securely, mounted at runtime |
| **Container Registry** | Stores built Docker images |

---

## Key Design Decisions

1. **Raw PCM over WebSocket** — No base64 encoding, no intermediate formats. Binary audio frames flow directly from microphone to Gemini and back, minimizing latency.

2. **Subprotocol authentication** — JWT token is passed as a WebSocket subprotocol during the handshake, avoiding the need for a separate auth step after connection.

3. **Tool calling for structured output** — Instead of parsing free-text responses, Gemini's native function calling ensures reliable, structured form field extraction with field name, value, and confidence score.

4. **Continuous background receiver** — An `asyncio.create_task` loop continuously reads from the Gemini Live session, enabling true real-time streaming without blocking the WebSocket handler.

5. **Frontend VAD** — Voice Activity Detection runs on the client side to detect silence, giving the system fast turn-taking without server round-trips.

---

## Supported Form Fields

| Field | Format | Example |
|-------|--------|---------|
| Full Name | As per PAN card | Vinayak Maskar |
| PAN Number | AAAAA9999A (5 letters, 4 digits, 1 letter) | ABCDE1234F |
| Date of Birth | DD/MM/YYYY | 15/08/1995 |
| State | Any Indian state | Maharashtra |
| Preferred Language | en, hi, mr, ta, te, bn, gu, kn, ml, pa | hi |

---

## Environment Variables / Secrets

Copy `secrets.json.example` to `secrets.json` and fill in:

| Key | Required | Description |
|-----|----------|-------------|
| `GEMINI_API_KEY` | **Yes** | Your Google Gemini API key |
| `SECRET_KEY` | Yes | Django secret key |
| `JWT_SECRET_KEY` | Yes | Key for signing JWT tokens |
| `GEMINI_MODEL` | No | Model name (default: `gemini-2.5-flash-native-audio-latest`) |

---

## Cloud Run Deployment (Automated)

The entire application is deployed to **Google Cloud Run** using the included `deploy.sh` script — infrastructure-as-code for fully automated deployment.

**Live URL:** [https://voice-chatbot-backend-7uucccu35q-el.a.run.app](https://voice-chatbot-backend-7uucccu35q-el.a.run.app)

**WebSocket:** `wss://voice-chatbot-backend-7uucccu35q-el.a.run.app/ws/voice-chat/?stage=basic_details`

### Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud` CLI)
- A GCP project with billing enabled

### Deploy (single command)

```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build frontend
cd frontend && npx expo export --platform web && cd ..

# Run the automated deployment script
./deploy.sh
```

### What `deploy.sh` does

1. Enables required GCP APIs (Cloud Run, Container Registry, Cloud Build, Secret Manager)
2. Uploads `secrets.json` to Secret Manager as `app-secrets`
3. Builds the Docker container via **Cloud Build** (no local Docker needed)
4. Deploys to **Cloud Run** with WebSocket support (Daphne ASGI)
5. Mounts secrets securely at `/secrets/secrets.json`
6. Prints the live URL and WebSocket endpoint

### Deployment architecture

| Component | Detail |
|-----------|--------|
| **Container** | `python:3.11-slim` + Daphne ASGI on port 8080 |
| **Frontend** | Expo web build served from Django at `/` |
| **Secrets** | Mounted from Secret Manager (never in container image) |
| **Scaling** | 0–3 instances, 512 MB RAM, 1 vCPU |
| **Region** | `asia-south1` (Mumbai) |
| **WebSockets** | Fully supported on Cloud Run (300s timeout) |
| **Auth** | Public access (`--allow-unauthenticated`) |

### Deployment files in this repo

| File | Purpose |
|------|---------|
| `deploy.sh` | Automated Cloud Run deployment script |
| `Dockerfile` | Production container definition |
| `.gcloudignore` | Controls which files are sent to Cloud Build |
| `.dockerignore` | Controls which files go into the Docker image |

---

## Team

- **Vinayak Maskar** — [GitHub](https://github.com/vinayakmaskar)

---

## License

This project was built for the [Gemini Live Agent Challenge](https://geminiliveagentchallenge.devpost.com/).
