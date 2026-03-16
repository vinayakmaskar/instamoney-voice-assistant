/**
 * WebSocket client for voice chatbot with subprotocol authentication.
 */
class WebSocketClient {
  constructor(token, stage, baseUrl = 'wss://voice-chatbot-backend-7uucccu35q-el.a.run.app') {
    this.token = token;
    this.stage = stage;
    this.baseUrl = baseUrl;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.listeners = {};
    this.connected = false;
  }

  connect() {
    if (!this.token) {
      console.error('❌ No authentication token found');
      this.emit('error', new Error('No authentication token'));
      return;
    }

    try {
      // Connect with token as subprotocol
      const wsUrl = `${this.baseUrl}/ws/voice-chat/?stage=${this.stage}`;
      console.log('🔌 Connecting to:', wsUrl);
      this.ws = new WebSocket(wsUrl, [this.token]);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected, readyState:', this.ws.readyState);
        this.connected = true;
        this.reconnectAttempts = 0;
        this.emit('open');
      };

      this.ws.onmessage = async (event) => {
        try {
          if (typeof event.data === 'string') {
            const data = JSON.parse(event.data);
            console.log('📨 [WEBSOCKET] Received text message:', data.type);
            this.emit('message', data);
          } else {
            // Handle binary data (audio chunks from backend)
            // Browser WebSocket receives binary as Blob, need to convert to ArrayBuffer
            let audioBuffer;
            if (event.data instanceof Blob) {
              console.log(`🔊 [WEBSOCKET] Received Blob: ${event.data.size} bytes, converting to ArrayBuffer...`);
              audioBuffer = await event.data.arrayBuffer();
              console.log(`✅ [WEBSOCKET] Converted to ArrayBuffer: ${audioBuffer.byteLength} bytes`);
            } else if (event.data instanceof ArrayBuffer) {
              console.log(`🔊 [WEBSOCKET] Received ArrayBuffer: ${event.data.byteLength} bytes`);
              audioBuffer = event.data;
            } else {
              console.error('❌ [WEBSOCKET] Unknown binary data type:', event.data.constructor.name);
              return;
            }
            
            console.log('🔊 [WEBSOCKET] Emitting "audio" event...');
            this.emit('audio', audioBuffer);
            console.log('✅ [WEBSOCKET] "audio" event emitted');
          }
        } catch (error) {
          console.error('❌ [WEBSOCKET] Error processing message:', error);
          this.emit('error', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error event:', error);
        console.error('❌ WebSocket readyState:', this.ws?.readyState);
        console.error('❌ WebSocket URL:', wsUrl);
        this.connected = false;
        this.emit('error', error || new Error('WebSocket connection failed'));
      };

      this.ws.onclose = (event) => {
        console.log('🔌 WebSocket closed:', event.code, event.reason || 'No reason');
        this.connected = false;
        this.emit('close', event);

        if (event.code === 4001) {
          console.error('❌ Authentication failed (4001)');
          this.emit('authFailed');
        } else if (event.code === 1006) {
          console.error('❌ Connection closed abnormally (1006) - server may not be running');
          this.emit('error', new Error('Connection closed - server may not be running'));
        } else if (event.code !== 1000) {
          // Not a normal closure, attempt reconnect
          console.log('⚠️ Unexpected close code:', event.code);
          this.attemptReconnect();
        }
      };
    } catch (error) {
      console.error('❌ Error creating WebSocket:', error);
      this.emit('error', error);
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      if (typeof data === 'string') {
        this.ws.send(data);
      } else {
        this.ws.send(JSON.stringify(data));
      }
    } else {
      console.warn('WebSocket is not open');
    }
  }

  sendText(text) {
    this.send({
      type: 'text_message',
      text: text,
    });
  }

  sendAudio(audioBlob) {
    // Convert blob to base64 and send
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64Audio = reader.result.split(',')[1];
      this.send({
        type: 'audio_chunk',
        data: base64Audio,
        format: 'webm',
        timestamp: Date.now(),
      });
    };
    reader.readAsDataURL(audioBlob);
  }

  sendBinaryAudio(audioData) {
    // Send binary audio directly
    // Can receive either ArrayBuffer (from Web Audio API) or Blob (from MediaRecorder)
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      if (audioData instanceof ArrayBuffer) {
        // Already an ArrayBuffer - send directly
        this.ws.send(audioData);
        // Only log occasionally to avoid spam
        if (Math.random() < 0.05) {
          console.log(`📤 [WS->BE] Sent ${audioData.byteLength} bytes PCM audio`);
        }
      } else if (audioData instanceof Blob) {
        // Convert Blob to ArrayBuffer and send
        audioData.arrayBuffer().then(buffer => {
          this.ws.send(buffer);
          console.log(`📤 [WS->BE] Sent ${buffer.byteLength} bytes audio (from Blob)`);
        }).catch(error => {
          console.error('❌ [WS->BE] Error converting Blob to ArrayBuffer:', error);
        });
      } else {
        console.error('❌ [WS->BE] Invalid audio data type:', typeof audioData);
      }
    } else {
      console.warn('⚠️ [WS->BE] WebSocket not open, cannot send audio');
    }
  }
  
  sendAudioChunk(audioChunk) {
    // Send audio chunk (for streaming)
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(audioChunk);
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = 1000 * this.reconnectAttempts;
      console.log(`Reconnecting in ${delay}ms... (Attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, delay);
    }
  }

  close() {
    if (this.ws) {
      this.ws.close(1000, 'Normal closure');
    }
  }

  isConnected() {
    return this.connected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

export default WebSocketClient;

