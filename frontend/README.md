# Voice Chatbot Frontend - React Native

React Native frontend for the voice chatbot application with Basic Details form.

## Setup

### Prerequisites

- Node.js 16+
- Expo CLI
- React Native development environment

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

3. Run on your device:
- iOS: Press `i` in the terminal or scan QR code with Expo Go app
- Android: Press `a` in the terminal or scan QR code with Expo Go app

## Configuration

Update the WebSocket URL in `src/services/websocket.js`:

```javascript
const client = new WebSocketClient(token, 'basic_details', 'ws://your-backend-url:8000');
```

## Features

- Basic Details form with all required fields
- Voice chatbot integration
- Real-time WebSocket communication
- Audio recording support
- Multi-language support
- Form field auto-fill from chatbot suggestions

## Components

- `BasicDetailsForm`: Main form component
- `VoiceChatbot`: Chatbot interface component
- `WebSocketClient`: WebSocket connection handler
- `AudioRecorder`: Audio recording utility

## Usage

1. Login to get authentication token (implement login screen)
2. Token is stored in AsyncStorage
3. Form connects to WebSocket automatically
4. Use voice or text to interact with chatbot
5. Chatbot can suggest form field values

## Notes

- Audio recording requires microphone permissions
- WebSocket uses subprotocol authentication
- Form data is stored in component state
- Chatbot suggestions automatically fill form fields

