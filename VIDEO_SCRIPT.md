# Demo Video Script — InstaMoney (< 4 minutes)

## Recording Tips
- Use screen recording (QuickTime or OBS)
- Record your voice narrating over the demo
- Show both the browser (frontend) AND terminal (backend logs) side by side
- Make sure audio is clear — judges need to hear the bot's voice responses

---

## [0:00 – 0:30] THE PROBLEM (30 seconds)

**Show:** A traditional loan form on a mobile screen (can be a screenshot)

**Narrate:**
> "In India, over 800 million people access the internet on their phones. But traditional loan forms are a nightmare — tiny text fields, confusing formats like PAN numbers, and everything in English. For hundreds of millions who speak Hindi, Marathi, Tamil, or other languages, this is a barrier to financial access."

**Show:** Transition to InstaMoney app

> "We built InstaMoney — a voice-powered loan assistant where you just talk to fill your form. In any language."

---

## [0:30 – 1:00] THE SOLUTION (30 seconds)

**Show:** The InstaMoney UI — the dark glassmorphism form with the mic button

**Narrate:**
> "InstaMoney uses Gemini's Live API for real-time, bidirectional audio streaming. No 'record and send' — it's a live conversation. The AI listens, understands, and auto-fills form fields as you speak."

**Show:** Point out the 5 form fields (Full Name, PAN, DOB, State, Language)

> "Let me show you how it works."

---

## [1:00 – 3:00] LIVE DEMO (2 minutes)

### Demo 1: Basic Flow (English) [1:00 – 1:45]

**Action:** Click the mic button

**Show:** Bot greets in Hindi: "Namaste! InstaMoney mein aapka swagat hai..."

**Narrate:** "The bot greets in Hindi by default — this is India-first."

**Action:** Say in English: "My name is Vinayak Maskar"

**Show:** 
- Form field "Full Name" auto-fills with green animation + checkmark
- Bot confirms briefly: "Done. PAN number?"

**Action:** Say: "My PAN is GJOPM0454F"

**Show:** PAN field auto-fills

**Action:** Say: "26 April 2002"

**Show:** DOB field auto-fills as "2002-04-26"

**Action:** Say: "Maharashtra"

**Show:** State field auto-fills

**Action:** Say: "Hindi"

**Show:** Language field auto-fills. All 5 fields now have green checkmarks. Completion shows "5/5".

### Demo 2: Language Switching [1:45 – 2:15]

**Narrate:** "Now watch — I'll switch to Hindi mid-conversation."

**Action:** Say in Hindi: "Mera naam badlo, Raj Kumar rakhdo"

**Show:** Bot responds IN HINDI, updates the name field

**Narrate:** "The bot detected I switched to Hindi and immediately responded in Hindi. It supports 10 Indian languages."

### Demo 3: Barge-in [2:15 – 2:30]

**Narrate:** "And users can interrupt the bot mid-speech — barge-in."

**Action:** Let bot start talking, then interrupt mid-sentence with your own speech

**Show:** Bot stops talking, listens to user

**Narrate:** "Just like a real conversation."

### Demo 4: Error Handling [2:30 – 2:45]

**Action:** Say: "My state is California"

**Show:** Bot responds: "That state is not available. Please say an Indian state name."

**Narrate:** "The bot validates inputs and asks again if something doesn't match."

---

## [2:45 – 3:30] ARCHITECTURE (45 seconds)

**Show:** Architecture diagram image

**Narrate:**
> "Under the hood: The frontend captures PCM audio at 24kHz and streams it over WebSocket to our Django backend on Cloud Run. The backend forwards audio directly to Gemini's Live API using the Google GenAI SDK."

> "Gemini processes speech in real-time and uses function calling — specifically our fill_form_field tool — to extract structured form data with confidence scores. Audio responses stream back through the same pipeline."

> "Everything is deployed on Google Cloud — Cloud Run for the backend, Cloud Build for CI, and Secret Manager for credentials. The entire deployment is automated with a single script."

---

## [3:30 – 3:55] IMPACT & CLOSE (25 seconds)

**Show:** The completed form with all 5 green checkmarks

**Narrate:**
> "InstaMoney makes financial services accessible to 1.4 billion Indians in their own language. No typing, no confusion, just a conversation."

> "Built with Gemini Live API, Google GenAI SDK, and Google Cloud Run for the Gemini Live Agent Challenge."

> "Thank you!"

---

## Checklist Before Recording
- [ ] Backend running (Daphne on port 8000)
- [ ] Frontend running (Expo on port 8081)
- [ ] JWT token is valid and not expired
- [ ] Microphone permissions granted in browser
- [ ] Screen recording software ready
- [ ] Architecture diagram image open in a tab
- [ ] Practice the flow once before recording
- [ ] Keep it under 4 minutes!
