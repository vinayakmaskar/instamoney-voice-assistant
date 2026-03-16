/**
 * Audio recorder for capturing microphone input.
 */
import { Audio } from 'expo-av';

class AudioRecorder {
  constructor() {
    this.recording = null;
    this.isRecording = false;
    this.audioChunks = [];
    this.onDataCallback = null;
  }

  async start() {
    try {
      // Request permissions
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        throw new Error('Microphone permission not granted');
      }

      // Set audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Create recording
      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY,
        (status) => {
          // Handle recording status updates
          if (status.isRecording) {
            this.isRecording = true;
          }
        }
      );

      this.recording = recording;
      console.log('🎤 Recording started');
    } catch (error) {
      console.error('Error starting recording:', error);
      throw error;
    }
  }

  async stop() {
    try {
      if (!this.recording) {
        return null;
      }

      await this.recording.stopAndUnloadAsync();
      const uri = this.recording.getURI();
      this.recording = null;
      this.isRecording = false;

      console.log('🛑 Recording stopped:', uri);
      return uri;
    } catch (error) {
      console.error('Error stopping recording:', error);
      throw error;
    }
  }

  async pause() {
    try {
      if (this.recording) {
        await this.recording.pauseAsync();
        this.isRecording = false;
      }
    } catch (error) {
      console.error('Error pausing recording:', error);
    }
  }

  async resume() {
    try {
      if (this.recording) {
        await this.recording.startAsync();
        this.isRecording = true;
      }
    } catch (error) {
      console.error('Error resuming recording:', error);
    }
  }

  isRecordingActive() {
    return this.isRecording;
  }
}

export default AudioRecorder;

