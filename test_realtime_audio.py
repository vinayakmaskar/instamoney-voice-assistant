"""
Test real-time audio streaming end-to-end.
Simulates frontend sending audio chunks continuously.
"""
import asyncio
import websockets
import base64
import json
import time

# Test token (same as frontend)
TEST_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMSIsImV4cCI6MTc2NzU4MzEyOSwiaWF0IjoxNzY3NDk2NzI5fQ.L0zcKDg_c71wcqVzBurLBBMn2QaeR3wG0wl8GaYXHyI'

async def create_dummy_webm_audio():
    """Create dummy WebM audio data for testing."""
    # Create a small dummy WebM header + data
    # In real scenario, this would be actual WebM audio from MediaRecorder
    dummy_audio = b'\x1a\x45\xdf\xa3'  # WebM EBML header start
    dummy_audio += b'\x01\x00\x00\x00\x00\x00\x00' * 100  # Dummy data
    return dummy_audio

async def test_realtime_streaming():
    """Test real-time bidirectional audio streaming."""
    print("=" * 60)
    print("🧪 REAL-TIME AUDIO STREAMING TEST")
    print("=" * 60)
    
    uri = f"ws://localhost:8000/ws/voice-chat/?stage=basic_details"
    
    try:
        print("\n🔌 Connecting to WebSocket...")
        async with websockets.connect(
            uri,
            subprotocols=[TEST_TOKEN],
            ping_interval=20,
            ping_timeout=10
        ) as websocket:
            print("✅ WebSocket connected!")
            
            # Wait for connection confirmation
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📨 Received: {data.get('type')} - {data.get('message')}")
                if data.get('type') != 'connection_established':
                    print("⚠️ Unexpected response")
                    return
            except asyncio.TimeoutError:
                print("⚠️ No connection confirmation received")
                return
            
            print("\n🎤 Starting real-time audio streaming...")
            print("   Sending audio chunks every 100ms (simulating continuous speech)")
            
            # Start receiving responses in background
            receive_task = asyncio.create_task(receive_responses(websocket))
            
            # Send audio chunks continuously (simulating user speaking)
            chunk_count = 0
            for i in range(20):  # Send 20 chunks (2 seconds of audio)
                audio_data = await create_dummy_webm_audio()
                await websocket.send(audio_data)
                chunk_count += 1
                print(f"📤 Sent audio chunk {chunk_count} ({len(audio_data)} bytes)")
                
                # Wait 100ms between chunks (real-time rate)
                await asyncio.sleep(0.1)
            
            print(f"\n✅ Sent {chunk_count} audio chunks")
            print("🔄 Waiting for responses (10 seconds)...")
            
            # Wait for responses
            await asyncio.sleep(10)
            
            # Cancel receive task
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
            
            print("\n✅ Test completed!")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def receive_responses(websocket):
    """Continuously receive audio responses from backend."""
    audio_chunks_received = 0
    total_bytes = 0
    
    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                
                # Check if binary (audio) or text (JSON)
                if isinstance(message, bytes):
                    audio_chunks_received += 1
                    total_bytes += len(message)
                    print(f"🔊 Received audio chunk {audio_chunks_received}: {len(message)} bytes")
                else:
                    data = json.loads(message)
                    print(f"📨 Received message: {data.get('type')}")
                    
            except asyncio.TimeoutError:
                # Timeout is expected - continue waiting
                continue
            except websockets.exceptions.ConnectionClosed:
                print("🔌 WebSocket connection closed")
                break
                
    except asyncio.CancelledError:
        print(f"\n📊 Summary: Received {audio_chunks_received} audio chunks, {total_bytes} bytes total")
    except Exception as e:
        print(f"❌ Error receiving responses: {e}")

if __name__ == "__main__":
    asyncio.run(test_realtime_streaming())

