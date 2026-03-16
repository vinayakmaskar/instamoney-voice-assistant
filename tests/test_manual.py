"""
Manual test script for testing voice chatbot with both servers running.
Run this after starting Django server and frontend.
"""
import asyncio
import websockets
import json
import jwt
from datetime import datetime, timedelta
from services.security import JWT_SECRET_KEY, JWT_ALGORITHM


async def test_websocket_connection():
    """Test WebSocket connection manually."""
    
    # Create test token
    payload = {
        'user_id': '1',
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    uri = f"ws://localhost:8000/ws/voice-chat/?stage=basic_details"
    
    print("=" * 60)
    print("VOICE CHATBOT MANUAL TEST")
    print("=" * 60)
    
    try:
        async with websockets.connect(uri, subprotocols=[token]) as websocket:
            print("✅ Connected to WebSocket")
            
            # Receive connection established
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 Received: {data}")
            
            # Test 1: Basic text message
            print("\n--- Test 1: Basic Text Message ---")
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': 'Hello, I need help with the form'
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            
            # Test 2: PAN Validation (Valid)
            print("\n--- Test 2: PAN Validation (Valid) ---")
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': 'My PAN number is ABCDE1234F'
            }))
            for _ in range(3):
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    print(f"Response: {data}")
                    if data.get('type') == 'form_suggestion':
                        break
                except:
                    break
            
            # Test 3: PAN Validation (Invalid)
            print("\n--- Test 3: PAN Validation (Invalid) ---")
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': 'My PAN is 12345'
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            
            # Test 4: DOB Validation (Valid)
            print("\n--- Test 4: DOB Validation (Valid) ---")
            dob = (datetime.now() - timedelta(days=365*25)).strftime("%d/%m/%Y")
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': f'My date of birth is {dob}'
            }))
            for _ in range(3):
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    print(f"Response: {data}")
                    if data.get('type') == 'form_suggestion':
                        break
                except:
                    break
            
            # Test 5: DOB Validation (Underage)
            print("\n--- Test 5: DOB Validation (Underage) ---")
            dob = (datetime.now() - timedelta(days=365*16)).strftime("%d/%m/%Y")
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': f'My date of birth is {dob}'
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            
            # Test 6: States List
            print("\n--- Test 6: States List Request ---")
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': 'What are the Indian states?'
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            
            # Test 7: Off-topic Question
            print("\n--- Test 7: Off-topic Question ---")
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': 'What is my loan amount?'
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            
            # Test 8: Heartbeat
            print("\n--- Test 8: Heartbeat Ping ---")
            await websocket.send(json.dumps({
                'type': 'ping'
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            
            # Test 9: Empty Message
            print("\n--- Test 9: Empty Message ---")
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': ''
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            
            print("\n" + "=" * 60)
            print("✅ All tests completed!")
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("Starting manual WebSocket tests...")
    print("Make sure Django server is running on localhost:8000")
    print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(test_websocket_connection())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")

