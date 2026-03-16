/**
 * Voice Chatbot Component
 * Modern Floating Action Button with Status Card
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Platform,
  ActivityIndicator,
  Animated,
  Easing,
} from 'react-native';
import WebSocketClient from '../services/websocket';
import { colors, spacing, borderRadius, typography } from '../styles/theme';

let AudioRecorder;
if (Platform.OS === 'web') {
  class WebAudioRecorder {
    constructor(wsClient) {
      this.audioContext = null;
      this.mediaStream = null;
      this.processor = null;
      this.isRecording = false;
      this.wsClient = wsClient;
      this.chunksSent = 0;
      this.lastLogTime = 0;
      
      this.silenceThreshold = 0.01;
      this.silenceDuration = 800;
      this.lastSoundTime = Date.now();
      this.isSpeaking = false;
      this.vadCheckInterval = null;
    }

    async start() {
      try {
        console.log('🎤 [MIC] Requesting microphone access...');
        
        this.mediaStream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            channelCount: 1,
            sampleRate: 24000,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          }
        });
        
        console.log('✅ [MIC] Microphone access granted!');
        
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
          sampleRate: 24000
        });
        console.log(`✅ [MIC] AudioContext created, state: ${this.audioContext.state}`);
        
        if (this.audioContext.state === 'suspended') {
          await this.audioContext.resume();
        }
        
        const source = this.audioContext.createMediaStreamSource(this.mediaStream);
        this.processor = this.audioContext.createScriptProcessor(2048, 1, 1);
        
        this.processor.onaudioprocess = (event) => {
          if (!this.isRecording) return;
          
          const inputBuffer = event.inputBuffer;
          const inputData = inputBuffer.getChannelData(0);
          
          let sum = 0;
          for (let i = 0; i < inputData.length; i++) {
            sum += inputData[i] * inputData[i];
          }
          const rms = Math.sqrt(sum / inputData.length);
          
          if (rms > this.silenceThreshold) {
            this.lastSoundTime = Date.now();
            if (!this.isSpeaking) {
              this.isSpeaking = true;
              console.log('🎤 [VAD] Speech detected, streaming started');
            }
          }
          
          const pcmData = new Int16Array(inputData.length);
          for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]));
            pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
          }
          
          if (this.wsClient && this.wsClient.isConnected()) {
            this.chunksSent++;
            const now = Date.now();
            if (this.chunksSent <= 3 || now - this.lastLogTime > 2000) {
              console.log(`📤 [MIC] Chunk #${this.chunksSent} | RMS: ${rms.toFixed(4)}`);
              this.lastLogTime = now;
            }
            try {
              this.wsClient.sendBinaryAudio(pcmData.buffer);
            } catch (sendError) {
              console.error('❌ [MIC->WS] Failed to send audio:', sendError);
            }
          }
        };
        
        source.connect(this.processor);
        this.processor.connect(this.audioContext.destination);
        
        this.isRecording = true;
        this.chunksSent = 0;
        this.lastSoundTime = Date.now();
        this.isSpeaking = false;
        
        this.vadCheckInterval = setInterval(() => {
          if (this.isSpeaking) {
            const silenceTime = Date.now() - this.lastSoundTime;
            if (silenceTime >= this.silenceDuration) {
              console.log(`🔇 [VAD] Silence detected for ${silenceTime}ms, speech ended`);
              this.isSpeaking = false;
            }
          }
        }, 100);
        
        console.log('✅ [MIC] Recording started with VAD!');
        return true;
      } catch (error) {
        console.error('❌ [MIC] Error starting recording:', error);
        throw error;
      }
    }

    async stop() {
      console.log(`🛑 [MIC] Stopping recording... (sent ${this.chunksSent} chunks total)`);
      this.isRecording = false;
      
      if (this.vadCheckInterval) {
        clearInterval(this.vadCheckInterval);
        this.vadCheckInterval = null;
      }
      
      if (this.processor) {
        this.processor.disconnect();
        this.processor = null;
      }
      
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(track => track.stop());
        this.mediaStream = null;
      }
      
      if (this.audioContext) {
        await this.audioContext.close();
        this.audioContext = null;
      }
      
      console.log('✅ [MIC] Recording stopped completely');
      return null;
    }

    isRecordingActive() {
      return this.isRecording;
    }
  }
  
  AudioRecorder = WebAudioRecorder;
} else {
  const ExpoAudioRecorder = require('../services/audioRecorder').default;
  AudioRecorder = ExpoAudioRecorder;
}

const VoiceChatbot = ({ onFormUpdate, onValidationResult }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioRecorder, setAudioRecorder] = useState(null);
  const [wsClient, setWsClient] = useState(null);
  const [connected, setConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [status, setStatus] = useState('Disconnected');
  const [lastFilledField, setLastFilledField] = useState(null);
  
  const audioChunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const audioQueueRef = useRef([]);
  const isPlayingRef = useRef(false);
  
  const TEST_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMSIsImV4cCI6MTc3NjIzMjY1MiwiaWF0IjoxNzczNjQwNjUyfQ.UV7EKh_e26JcSd_ennmN5jtCDMniFU_HqJOsbAytLoQ';

  useEffect(() => {
    return () => {
      if (wsClient) wsClient.close();
    };
  }, [wsClient]);

  const initializeWebSocket = () => {
    return new Promise((resolve, reject) => {
      try {
        console.log('🔌 Initializing WebSocket connection...');
        const token = TEST_TOKEN;
        if (!token) {
          reject(new Error('Token not available'));
          return;
        }

        const client = new WebSocketClient(token, 'basic_details', 'ws://localhost:8000');
        
        let connectionTimeout;
        let resolved = false;
        
        connectionTimeout = setTimeout(() => {
          if (!resolved && !client.isConnected()) {
            console.error('❌ Connection timeout after 5 seconds');
            reject(new Error('Connection timeout - server may not be running'));
          }
        }, 5000);
        
        client.on('open', () => {
          console.log('✅ WebSocket connected to backend');
          if (connectionTimeout) clearTimeout(connectionTimeout);
          resolved = true;
          setConnected(true);
          setWsClient(client);
          resolve(client);
        });

        client.on('message', (data) => {
          console.log('📨 Received message:', data.type);
          if (data.type === 'connection_established') {
            console.log('✅ Connection confirmed:', data.message);
            setConnected(true);
            setStatus('Connected');
          }
          handleWebSocketMessage(data);
        });

        console.log('🔊 [SETUP] Registering "audio" event handler...');
        client.on('audio', (audioData) => {
          console.log('🔊 [EVENT] "audio" event fired!');
          if (audioData) {
            handleAudioChunk(audioData);
          }
        });
        console.log('✅ [SETUP] "audio" event handler registered');

        client.on('error', (error) => {
          console.error('❌ WebSocket error:', error);
          if (connectionTimeout) clearTimeout(connectionTimeout);
          if (!resolved) {
            resolved = true;
            reject(new Error(error.message || 'WebSocket connection failed.'));
          }
          setConnected(false);
          setIsProcessing(false);
          setIsConnecting(false);
        });

        client.on('close', (event) => {
          console.log('🔌 WebSocket closed:', event.code, event.reason);
          if (connectionTimeout) clearTimeout(connectionTimeout);
          setConnected(false);
          setWsClient(null);
          setIsProcessing(false);
          setIsConnecting(false);
        });

        client.on('authFailed', () => {
          console.error('❌ Authentication failed');
          if (connectionTimeout) clearTimeout(connectionTimeout);
          if (!resolved) {
            resolved = true;
            reject(new Error('Authentication failed - invalid token'));
          }
          setConnected(false);
          setIsProcessing(false);
          setIsConnecting(false);
          Alert.alert('Authentication Failed', 'Please check your token');
        });

        console.log('🔌 Attempting to connect...');
        client.connect();
      } catch (error) {
        console.error('❌ Error initializing WebSocket:', error);
        setIsProcessing(false);
        reject(error);
      }
    });
  };

  const audioChunksReceivedRef = useRef(0);
  const nextPlayTimeRef = useRef(0);
  
  const stopBotPlayback = () => {
    console.log('🛑 [STOP] Stopping bot playback...');
    const queueSize = audioQueueRef.current.length;
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    nextPlayTimeRef.current = 0;
    console.log(`✅ [BARGE-IN] Cleared ${queueSize} queued chunks`);
  };
  
  const handleAudioChunk = (audioData) => {
    audioChunksReceivedRef.current++;
    const chunkNum = audioChunksReceivedRef.current;
    
    if (!audioData || audioData.byteLength === 0) return;
    
    if (chunkNum <= 3 || chunkNum % 10 === 0) {
      console.log(`📥 [RECV #${chunkNum}] ${audioData.byteLength} bytes`);
    }
    
    if (Platform.OS === 'web') {
      playPCMAudioChunk(audioData);
    }
  };

  const audioChunksPlayedRef = useRef(0);
  
  const playNextAudio = useCallback(() => {
    isPlayingRef.current = false;
    
    if (audioQueueRef.current.length > 0) {
      const nextSource = audioQueueRef.current.shift();
      isPlayingRef.current = true;
      nextSource.onended = playNextAudio;
      
      try {
        nextSource.start(0);
      } catch (e) {
        console.error('❌ [QUEUE] Error playing next chunk:', e);
        playNextAudio();
      }
    }
  }, []);
  
  const playPCMAudioChunk = useCallback(async (pcmChunk) => {
    try {
      audioChunksPlayedRef.current++;
      const chunkNum = audioChunksPlayedRef.current;
      
      if (!pcmChunk || pcmChunk.byteLength === 0 || pcmChunk.byteLength < 100) return;
      
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
          sampleRate: 24000
        });
      }
      
      const audioContext = audioContextRef.current;
      
      if (audioContext.state === 'suspended') {
        await audioContext.resume();
      }
      
      if (audioContext.state !== 'running') return;
      
      const sampleRate = 24000;
      const frameCount = pcmChunk.byteLength / 2;
      
      const audioBuffer = audioContext.createBuffer(1, frameCount, sampleRate);
      const channelData = audioBuffer.getChannelData(0);
      const pcmData = new Int16Array(pcmChunk);
      
      for (let i = 0; i < frameCount && i < pcmData.length; i++) {
        channelData[i] = pcmData[i] / 32768.0;
      }
      
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      
      const wasPlaying = isPlayingRef.current;
      
      if (wasPlaying) {
        source.onended = playNextAudio;
        audioQueueRef.current.push(source);
      } else {
        isPlayingRef.current = true;
        source.onended = playNextAudio;
        try {
          source.start(0);
        } catch (startError) {
          isPlayingRef.current = false;
        }
      }
    } catch (error) {
      isPlayingRef.current = false;
    }
  }, [playNextAudio]);

  const playAccumulatedAudio = () => {
    if (Platform.OS === 'web' && audioChunksRef.current.length > 0) {
      try {
        const totalSize = audioChunksRef.current.reduce((sum, chunk) => sum + chunk.byteLength, 0);
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/pcm' });
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          audioChunksRef.current = [];
        };
        audio.onerror = () => {
          try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const sampleRate = 24000;
            const frameCount = totalSize / 2;
            const audioBuffer = audioContext.createBuffer(1, frameCount, sampleRate);
            const channelData = audioBuffer.getChannelData(0);
            const combinedBuffer = new ArrayBuffer(totalSize);
            let offset = 0;
            for (const chunk of audioChunksRef.current) {
              new Uint8Array(combinedBuffer).set(new Uint8Array(chunk), offset);
              offset += chunk.byteLength;
            }
            const pcmData = new Int16Array(combinedBuffer);
            for (let i = 0; i < frameCount; i++) {
              channelData[i] = pcmData[i] / 32768.0;
            }
            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            source.onended = () => { audioChunksRef.current = []; audioContext.close(); };
            source.start(0);
            setIsProcessing(false);
          } catch (webAudioError) {
            console.error('❌ Error with Web Audio API:', webAudioError);
          }
          URL.revokeObjectURL(audioUrl);
        };
        audio.play().catch(() => { audioChunksRef.current = []; });
      } catch (error) {
        audioChunksRef.current = [];
      }
    }
  };

  const FIELD_LABELS = {
    fullName: 'Full Name',
    panNumber: 'PAN Number',
    dateOfBirth: 'Date of Birth',
    state: 'State',
    preferredLanguage: 'Language',
  };

  const handleWebSocketMessage = (data) => {
    console.log('📨 Received message:', data.type);
    
    if (data.type === 'form_suggestion' && onFormUpdate) {
      const { field, value, display_value, confidence } = data;
      console.log(`✅ Auto-filling ${field}: ${display_value || value} (${confidence} confidence)`);
      
      const fieldMap = {
        'panNumber': 'panNumber',
        'dateOfBirth': 'dateOfBirth',
        'fullName': 'fullName',
        'state': 'state',
        'preferredLanguage': 'preferredLanguage',
      };
      const mappedField = fieldMap[field] || field;
      onFormUpdate(mappedField, value);
      
      setLastFilledField(FIELD_LABELS[mappedField] || mappedField);
      setTimeout(() => setLastFilledField(null), 3000);
      
      setIsProcessing(false);
    } else if (data.type === 'validation_result' && onValidationResult) {
      const fieldMap = { 'panNumber': 'panNumber', 'dateOfBirth': 'dateOfBirth' };
      const field = fieldMap[data.field] || data.field;
      onValidationResult(field, data.is_valid, data.message);
      setIsProcessing(false);
    } else if (data.type === 'response_text') {
      if (data.is_final) setIsProcessing(false);
    } else if (data.type === 'audio_response_complete') {
      setIsProcessing(false);
      playAccumulatedAudio();
    } else if (data.type === 'reconnecting') {
      setStatus(`Reconnecting... (${data.attempt})`);
    } else if (data.type === 'reconnected') {
      setStatus('Connected');
      setConnected(true);
    } else if (data.type === 'error') {
      console.error('❌ Error from server:', data.message, data.error_code);
      if (data.error_code === 'MAX_RECONNECTS_REACHED') {
        Alert.alert('Connection Lost', 'Voice service disconnected. Please refresh the page.');
        setConnected(false);
        setIsRecording(false);
      }
      setIsProcessing(false);
    }
  };

  const handleVoiceButtonPress = async () => {
    try {
      if (Platform.OS === 'web') {
        try {
          if (!audioContextRef.current) {
            audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
          }
          if (audioContextRef.current.state === 'suspended') {
            await audioContextRef.current.resume();
          }
          audioChunksReceivedRef.current = 0;
          audioChunksPlayedRef.current = 0;
          audioQueueRef.current = [];
          isPlayingRef.current = false;
        } catch (audioError) {
          console.error('❌ [AUDIO] Failed to initialize AudioContext:', audioError);
        }
      }
      
      if (isRecording) {
        await stopRecording();
        return;
      }
      
      if (isProcessing || isConnecting) return;
      
      if (!wsClient || !wsClient.isConnected()) {
        setIsProcessing(true);
        setIsConnecting(true);
        
        try {
          const client = await initializeWebSocket();
          if (client && client.isConnected()) {
            setWsClient(client);
            setConnected(true);
            setIsConnecting(false);
            setIsProcessing(false);
            await startRecording(client);
          } else {
            setIsConnecting(false);
            setIsProcessing(false);
            throw new Error('Connection not established');
          }
        } catch (error) {
          setIsConnecting(false);
          setIsProcessing(false);
          Alert.alert('Connection Error', error.message || 'Failed to connect.');
        }
      } else {
        await startRecording(wsClient);
      }
    } catch (error) {
      setIsProcessing(false);
      setIsConnecting(false);
      Alert.alert('Error', 'An unexpected error occurred. Please try again.');
    }
  };

  const startRecording = async (client = null) => {
    try {
      const activeClient = client || wsClient;
      if (!activeClient || !activeClient.isConnected()) {
        Alert.alert('Error', 'Not connected to voice chatbot.');
        setIsProcessing(false);
        setIsConnecting(false);
        return;
      }

      const recorder = Platform.OS === 'web' 
        ? new AudioRecorder(activeClient)
        : new AudioRecorder();
      
      await recorder.start();
      setAudioRecorder(recorder);
      setIsRecording(true);
      setIsProcessing(false);
      setIsConnecting(false);
    } catch (error) {
      let errorMessage = 'Failed to start recording.';
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        errorMessage = 'Microphone permission denied.';
      } else if (error.name === 'NotFoundError') {
        errorMessage = 'No microphone found.';
      }
      Alert.alert('Recording Error', errorMessage);
      setIsRecording(false);
      setIsProcessing(false);
      setIsConnecting(false);
    }
  };

  const stopRecording = async () => {
    try {
      if (audioRecorder) {
        await audioRecorder.stop();
        setIsRecording(false);
        setAudioRecorder(null);
        setIsProcessing(true);
        
        setTimeout(() => {
          if (wsClient) {
            wsClient.close();
            setWsClient(null);
            setConnected(false);
          }
          setIsProcessing(false);
        }, 2000);
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
      setIsRecording(false);
      setIsProcessing(false);
      if (wsClient) { wsClient.close(); setWsClient(null); setConnected(false); }
    }
  };

  // Animations
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const rippleAnim = useRef(new Animated.Value(0)).current;
  const glowAnim = useRef(new Animated.Value(0)).current;
  
  useEffect(() => {
    if (isRecording) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.15, duration: 800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        ])
      );
      
      const ripple = Animated.loop(
        Animated.sequence([
          Animated.timing(rippleAnim, { toValue: 1, duration: 2000, easing: Easing.out(Easing.ease), useNativeDriver: true }),
          Animated.timing(rippleAnim, { toValue: 0, duration: 0, useNativeDriver: true }),
        ])
      );
      
      const glow = Animated.loop(
        Animated.sequence([
          Animated.timing(glowAnim, { toValue: 1, duration: 1200, useNativeDriver: false }),
          Animated.timing(glowAnim, { toValue: 0, duration: 1200, useNativeDriver: false }),
        ])
      );
      
      pulse.start();
      ripple.start();
      glow.start();
      
      return () => {
        pulse.stop();
        ripple.stop();
        glow.stop();
        pulseAnim.setValue(1);
        rippleAnim.setValue(0);
        glowAnim.setValue(0);
      };
    }
  }, [isRecording]);
  
  const handlePressIn = () => {
    Animated.spring(scaleAnim, { toValue: 0.88, friction: 5, useNativeDriver: true }).start();
  };
  
  const handlePressOut = () => {
    Animated.spring(scaleAnim, { toValue: 1, friction: 5, useNativeDriver: true }).start();
  };
  
  const getButtonColors = () => {
    if (isRecording) return ['#ef4444', '#dc2626'];
    if (isProcessing || isConnecting) return [colors.accent, colors.gradientEnd];
    return [colors.gradientStart, colors.gradientEnd];
  };

  const getStatusText = () => {
    if (isRecording) return 'Listening...';
    if (isConnecting) return 'Connecting...';
    if (isProcessing) return 'Processing...';
    return null;
  };

  const statusText = getStatusText();
  const isActive = isRecording || isProcessing || isConnecting;

  return (
    <View style={styles.container}>
      {/* Field filled notification */}
      {lastFilledField && (
        <View style={styles.fieldNotification}>
          <Text style={styles.fieldNotificationIcon}>{'\u2713'}</Text>
          <Text style={styles.fieldNotificationText}>{lastFilledField} filled</Text>
        </View>
      )}
      
      {/* Status card */}
      {statusText && (
        <View style={[
          styles.statusCard,
          isRecording && styles.statusCardRecording,
        ]}>
          {isRecording && (
            <View style={styles.waveContainer}>
              {[0, 1, 2, 3, 4].map(i => (
                <Animated.View
                  key={i}
                  style={[
                    styles.waveBar,
                    {
                      height: glowAnim.interpolate({
                        inputRange: [0, 1],
                        outputRange: [4 + i * 2, 12 + (4 - Math.abs(i - 2)) * 4],
                      }),
                      backgroundColor: isRecording ? colors.recording : colors.accent,
                    },
                  ]}
                />
              ))}
            </View>
          )}
          {(isProcessing || isConnecting) && (
            <ActivityIndicator size="small" color={colors.accent} style={{ marginRight: 8 }} />
          )}
          <Text style={[
            styles.statusText,
            isRecording && styles.statusTextRecording,
          ]}>
            {statusText}
          </Text>
        </View>
      )}
      
      {/* Ripple rings */}
      {isRecording && (
        <>
          <Animated.View
            style={[
              styles.ripple,
              {
                transform: [{
                  scale: rippleAnim.interpolate({ inputRange: [0, 1], outputRange: [1, 2.8] }),
                }],
                opacity: rippleAnim.interpolate({ inputRange: [0, 1], outputRange: [0.25, 0] }),
                borderColor: colors.recording,
              },
            ]}
          />
          <Animated.View
            style={[
              styles.ripple,
              {
                transform: [{
                  scale: rippleAnim.interpolate({ inputRange: [0, 1], outputRange: [1, 2] }),
                }],
                opacity: rippleAnim.interpolate({ inputRange: [0, 1], outputRange: [0.15, 0] }),
                borderColor: colors.recording,
              },
            ]}
          />
        </>
      )}
      
      {/* FAB */}
      <Animated.View
        style={[
          styles.buttonOuter,
          {
            transform: [
              { scale: Animated.multiply(scaleAnim, isRecording ? pulseAnim : 1) },
            ],
            shadowColor: isRecording ? colors.recording : colors.gradientStart,
          },
        ]}
      >
        <TouchableOpacity
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          onPress={async (e) => {
            if (e) { e.preventDefault(); e.stopPropagation(); }
            try { await handleVoiceButtonPress(); } catch (err) {
              Alert.alert('Error', err.message || 'Something went wrong');
              setIsProcessing(false);
              setIsConnecting(false);
            }
          }}
          disabled={(isProcessing || isConnecting) && !isRecording}
          activeOpacity={0.9}
          style={styles.buttonTouchable}
        >
          <View style={styles.buttonInner}>
            {(isProcessing || isConnecting) && !isRecording ? (
              <ActivityIndicator size={24} color="#fff" />
            ) : isRecording ? (
              <View style={styles.stopIcon} />
            ) : (
              <Text style={styles.micIcon}>{'\u{1F3A4}'}</Text>
            )}
          </View>
        </TouchableOpacity>
      </Animated.View>
      
      {/* Idle hint */}
      {!isActive && (
        <Text style={styles.hintText}>Tap to speak</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 32,
    right: 28,
    alignItems: 'center',
    zIndex: 1000,
  },
  fieldNotification: {
    position: 'absolute',
    bottom: 90,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.successGlow,
    borderWidth: 1,
    borderColor: 'rgba(52, 211, 153, 0.3)',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: borderRadius.round,
    gap: 6,
  },
  fieldNotificationIcon: {
    fontSize: 12,
    color: colors.success,
    fontWeight: '700',
  },
  fieldNotificationText: {
    fontSize: typography.sizes.sm,
    color: colors.success,
    fontWeight: '600',
  },
  statusCard: {
    position: 'absolute',
    bottom: 80,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(10, 10, 20, 0.9)',
    borderWidth: 1,
    borderColor: colors.glassBorder,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: borderRadius.round,
    minWidth: 130,
    justifyContent: 'center',
  },
  statusCardRecording: {
    borderColor: 'rgba(248, 113, 113, 0.3)',
    backgroundColor: 'rgba(248, 113, 113, 0.08)',
  },
  waveContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    marginRight: 10,
  },
  waveBar: {
    width: 3,
    borderRadius: 1.5,
    minHeight: 4,
  },
  statusText: {
    color: colors.textSecondary,
    fontSize: typography.sizes.sm,
    fontWeight: '600',
  },
  statusTextRecording: {
    color: colors.recording,
  },
  ripple: {
    position: 'absolute',
    width: 64,
    height: 64,
    borderRadius: 32,
    borderWidth: 2,
  },
  buttonOuter: {
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.5,
    shadowRadius: 16,
    elevation: 12,
  },
  buttonTouchable: {
    borderRadius: 32,
    overflow: 'hidden',
  },
  buttonInner: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.gradientStart,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  micIcon: {
    fontSize: 26,
  },
  stopIcon: {
    width: 20,
    height: 20,
    borderRadius: 4,
    backgroundColor: '#fff',
  },
  hintText: {
    marginTop: 8,
    fontSize: typography.sizes.xs,
    color: colors.textMuted,
    fontWeight: '500',
  },
});

export default VoiceChatbot;
