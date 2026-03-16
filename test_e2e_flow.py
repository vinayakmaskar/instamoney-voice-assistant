#!/usr/bin/env python3
"""
End-to-end test for voice chatbot flow.
Tests: WebSocket connection → Audio sending → Gemini Live API → Audio response
"""
import asyncio
import websockets
import json
import base64
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test token (same as in frontend)
TEST_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMSIsImV4cCI6MTc2NzU4MzEyOSwiaWF0IjoxNzY3NDk2NzI5fQ.L0zcKDg_c71wcqVzBurLBBMn2QaeR3wG0wl8GaYXHyI'

async def test_websocket_connection():
    """Test WebSocket connection with subprotocol authentication."""
    print("🔌 Testing WebSocket connection...")
    
    uri = "ws://localhost:8000/ws/voice-chat/?stage=basic_details"
    
    try:
        # Connect with token as subprotocol
        async with websockets.connect(
            uri,
            subprotocols=[TEST_TOKEN]
        ) as websocket:
            print("✅ WebSocket connected!")
            
            # Wait for connection_established message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"📨 Received: {data.get('type')} - {data.get('message')}")
                
                if data.get('type') == 'connection_established':
                    print("✅ Connection confirmed by server")
                    return websocket
                else:
                    print(f"⚠️ Unexpected message type: {data.get('type')}")
                    return None
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for connection confirmation")
                return None
                
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def create_dummy_audio():
    """Create a dummy WebM audio file for testing."""
    # Minimal valid WebM header + some dummy data
    # This is a very basic WebM structure - in real use, this would be actual recorded audio
    webm_header = b'\x1a\x45\xdf\xa3'  # EBML header
    webm_header += b'\x42\x86'  # EBMLVersion
    webm_header += b'\x42\xf7'  # EBMLReadVersion
    webm_header += b'\x42\xf2'  # EBMLMaxIDLength
    webm_header += b'\x42\xf3'  # EBMLMaxSizeLength
    webm_header += b'\x42\x82'  # DocType
    webm_header += b'\x86'  # DocTypeVersion
    webm_header += b'\x81\x01'  # DocTypeReadVersion
    
    # Add some dummy audio data
    dummy_audio = webm_header + b'\x00' * 5000  # 5KB of dummy data
    
    return dummy_audio

async def test_audio_sending(websocket):
    """Test sending audio data through WebSocket."""
    print("\n🎤 Testing audio sending...")
    
    try:
        # Create dummy audio
        audio_data = await create_dummy_audio()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        print(f"📤 Sending {len(audio_data)} bytes of audio data...")
        
        # Send audio as binary
        await websocket.send(audio_data)
        print("✅ Audio data sent")
        
        # Wait for responses
        print("⏳ Waiting for audio response...")
        response_count = 0
        audio_chunks_received = 0
        total_audio_size = 0
        
        try:
            while True:
                try:
                    # Wait for message (text or binary)
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_count += 1
                    
                    if isinstance(message, bytes):
                        # Binary audio chunk
                        audio_chunks_received += 1
                        total_audio_size += len(message)
                        print(f"🔊 Received audio chunk {audio_chunks_received}: {len(message)} bytes")
                    else:
                        # Text message
                        try:
                            data = json.loads(message)
                            print(f"📨 Received text message: {data.get('type')}")
                            
                            if data.get('type') == 'audio_response_complete':
                                print(f"✅ Audio response complete!")
                                print(f"   Total chunks: {data.get('chunks_received', 0)}")
                                print(f"   Total size: {data.get('total_size', 0)} bytes")
                                break
                            elif data.get('type') == 'error':
                                print(f"❌ Error from server: {data.get('message')}")
                                break
                        except json.JSONDecodeError:
                            print(f"⚠️ Received non-JSON text: {message[:100]}")
                    
                    # Safety limit
                    if response_count > 100:
                        print("⚠️ Reached response limit, stopping")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏱️ Timeout waiting for response")
                    if audio_chunks_received > 0:
                        print(f"✅ Still received {audio_chunks_received} audio chunks ({total_audio_size} bytes)")
                    break
                    
        except Exception as e:
            print(f"⚠️ Error receiving responses: {e}")
            if audio_chunks_received > 0:
                print(f"✅ Still received {audio_chunks_received} audio chunks ({total_audio_size} bytes)")
        
        print(f"\n📊 Test Results:")
        print(f"   Audio chunks received: {audio_chunks_received}")
        print(f"   Total audio size: {total_audio_size} bytes")
        print(f"   Total messages: {response_count}")
        
        return audio_chunks_received > 0
        
    except Exception as e:
        print(f"❌ Error sending audio: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_complete_flow():
    """Test the complete end-to-end flow."""
    print("=" * 60)
    print("🧪 END-TO-END FLOW TEST")
    print("=" * 60)
    
    # Step 1: Test WebSocket connection
    websocket = await test_websocket_connection()
    if not websocket:
        print("\n❌ TEST FAILED: Could not establish WebSocket connection")
        return False
    
    # Step 2: Test audio sending and receiving
    success = await test_audio_sending(websocket)
    
    # Step 3: Close connection
    try:
        await websocket.close()
        print("\n🔌 WebSocket connection closed")
    except:
        pass
    
    print("\n" + "=" * 60)
    if success:
        print("✅ END-TO-END TEST PASSED")
    else:
        print("❌ END-TO-END TEST FAILED")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(test_complete_flow())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

