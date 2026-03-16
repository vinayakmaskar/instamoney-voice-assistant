# Building a Voice-Powered Loan Assistant with Gemini Live API and Google Cloud

*Created for the #GeminiLiveAgentChallenge hackathon*

---

## The Problem

In India, over 800 million people access the internet primarily through their phones — and a significant number are not comfortable typing in English. Traditional loan application forms create a massive friction point: small text inputs, confusing field formats (PAN numbers, date formats), and English-only interfaces exclude a huge portion of the population.

What if users could just **talk** to fill out their loan application — in their own language?

## The Solution: InstaMoney

InstaMoney is a real-time, multilingual voice assistant that fills out loan application forms through natural speech. Users click a microphone button and simply talk. The AI listens, understands, extracts form field values, and auto-fills the form — all in real time with zero typing.

### What makes it special:

- **Truly live** — No "record and send." Audio streams bidirectionally between the user and Gemini in real time.
- **10 Indian languages** — Hindi, Marathi, Tamil, Telugu, Bengali, Gujarati, Kannada, Malayalam, Punjabi, and English. Switch languages mid-conversation and the bot follows immediately.
- **Barge-in** — Users can interrupt the bot mid-speech, just like a real conversation.
- **Smart form filling** — Gemini uses function calling (`fill_form_field`) to extract structured data with confidence scores.

## How We Built It with Google AI and Google Cloud

### Gemini Live API — The Core

The entire experience is powered by **Gemini 2.5 Flash Native Audio** through the **Google GenAI SDK**. We use the `bidiGenerateContent` Live API for true bidirectional audio streaming.

```python
import google.genai as genai

client = genai.Client(api_key=GEMINI_API_KEY)
session = client.aio.live.connect(
    model="gemini-2.5-flash-native-audio-latest",
    config={
        "response_modalities": ["AUDIO"],
        "tools": [fill_form_field_tool],
        "input_audio_transcription": {},
        "output_audio_transcription": {},
    }
)
```

Key architectural decisions:

1. **Raw PCM over WebSocket** — Audio flows as binary PCM (16-bit, 24kHz, mono) directly from the browser microphone to Gemini and back. No base64 encoding overhead.

2. **Tool calling for structured output** — Instead of parsing free-text, Gemini's native function calling ensures reliable field extraction:
   ```
   fill_form_field(field_name="fullName", value="Vinayak Maskar", confidence="high")
   ```

3. **Continuous background receiver** — An `asyncio.create_task` loop reads from the Gemini session continuously, enabling true real-time streaming without blocking.

### Google Cloud Run — Production Hosting

The backend runs on **Cloud Run** with **Daphne** (ASGI server) for WebSocket support. We automated the entire deployment with a single script:

- **Cloud Build** builds the Docker container
- **Secret Manager** stores API keys securely
- **Cloud Run** serves the ASGI app with auto-scaling (0 to 3 instances)

### The Frontend

Built with **React Native (Expo)** for cross-platform support. Features a glassmorphism UI with:
- Animated voice button with ripple effects
- Real-time waveform bars during recording
- Fields that light up green with checkmarks as the bot fills them
- Toast notifications for each auto-filled field

## The Stack

| Layer | Technology |
|-------|-----------|
| AI Model | Gemini 2.5 Flash Native Audio |
| AI SDK | Google GenAI SDK (`google-genai`) |
| Backend | Django Channels + Daphne |
| Hosting | Google Cloud Run |
| Secrets | Google Secret Manager |
| Build | Google Cloud Build |
| Frontend | React Native (Expo) |
| Audio | Web Audio API (PCM 24kHz) |

## Challenges We Faced

1. **PKCE and JWT auth over WebSocket** — WebSockets don't support HTTP headers, so we pass the JWT token as a WebSocket subprotocol during the handshake.

2. **Multilingual tool calling** — Gemini needed to extract Latin-script values from Hindi/Marathi speech. We solved this with detailed system prompt engineering and validation layers.

3. **Barge-in handling** — When the user interrupts, we need to stop audio playback immediately on the frontend while the backend handles the interruption event from the Live API.

4. **Auto-reconnection** — The Live API session can disconnect. We built a 3-retry auto-reconnect system with exponential backoff that's transparent to the user.

## What's Next

- Add more form stages (employment, income, documents)
- Camera-based PAN card reading using Gemini's vision capabilities
- Deploy on mobile (iOS/Android) using the same Expo codebase

## Try It

- **GitHub**: [github.com/vinayakmaskar/instamoney-voice-assistant](https://github.com/vinayakmaskar/instamoney-voice-assistant)

---

*This blog post was created for the purposes of entering the Gemini Live Agent Challenge hackathon. #GeminiLiveAgentChallenge*

*Built by Vinayak Maskar*
