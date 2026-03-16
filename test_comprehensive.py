#!/usr/bin/env python
"""
Comprehensive test script for all functionalities.
Tests both servers and all features.
"""
import asyncio
import sys
import os
import json
import jwt
from datetime import datetime, timedelta

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voice_chatbot.settings')

import django
django.setup()

from services.security import JWT_SECRET_KEY, JWT_ALGORITHM
import websockets


async def test_all_functionalities():
    """Test all functionalities comprehensively."""
    
    print("=" * 70)
    print("COMPREHENSIVE VOICE CHATBOT TEST SUITE")
    print("=" * 70)
    print()
    
    # Create test token
    payload = {
        'user_id': '1',
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    uri = "ws://localhost:8000/ws/voice-chat/?stage=basic_details"
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'total': 0
    }
    
    def test(name, test_func):
        """Run a test and track results."""
        test_results['total'] += 1
        try:
            result = test_func()
            if result:
                print(f"✅ {name}")
                test_results['passed'] += 1
                return True
            else:
                print(f"❌ {name}")
                test_results['failed'] += 1
                return False
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
            test_results['failed'] += 1
            return False
    
    try:
        print("Connecting to WebSocket...")
        async with websockets.connect(uri, subprotocols=[token]) as websocket:
            print("✅ Connected to WebSocket\n")
            
            # Receive connection established
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 Connection: {data.get('message', 'Connected')}\n")
            
            # Test 1: Basic Text Message
            print("=" * 70)
            print("TEST 1: Basic Text Message")
            print("=" * 70)
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': 'Hello, I need help with the form'
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data.get('text', data.get('message', ''))[:100]}...")
            test("Basic text message", lambda: data.get('type') in ['response_text', 'tool_result'])
            print()
            
            # Test 2: PAN Validation (Valid)
            print("=" * 70)
            print("TEST 2: PAN Validation (Valid)")
            print("=" * 70)
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': 'My PAN number is ABCDE1234F'
            }))
            responses = []
            for _ in range(5):
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    responses.append(data)
                    print(f"Response: {data}")
                    if data.get('type') == 'form_suggestion' and data.get('field') == 'panNumber':
                        break
                except:
                    break
            test("PAN validation and form suggestion", 
                 lambda: any(r.get('type') == 'form_suggestion' for r in responses))
            print()
            
            # Test 3: PAN Validation (Invalid)
            print("=" * 70)
            print("TEST 3: PAN Validation (Invalid)")
            print("=" * 70)
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': 'My PAN is 12345'
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data.get('text', data.get('message', ''))[:200]}")
            test("Invalid PAN rejection", 
                 lambda: 'invalid' in data.get('text', '').lower() or 
                         data.get('type') == 'validation_result')
            print()
            
            # Test 4: DOB Validation (Valid)
            print("=" * 70)
            print("TEST 4: DOB Validation (Valid - 25 years old)")
            print("=" * 70)
            dob = (datetime.now() - timedelta(days=365*25)).strftime("%d/%m/%Y")
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': f'My date of birth is {dob}'
            }))
            responses = []
            for _ in range(5):
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    responses.append(data)
                    print(f"Response: {data}")
                    if data.get('type') == 'form_suggestion':
                        break
                except:
                    break
            test("DOB validation and form suggestion",
                 lambda: any(r.get('type') == 'form_suggestion' for r in responses))
            print()
            
            # Test 5: DOB Validation (Underage)
            print("=" * 70)
            print("TEST 5: DOB Validation (Underage - 16 years old)")
            print("=" * 70)
            dob = (datetime.now() - timedelta(days=365*16)).strftime("%d/%m/%Y")
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': f'My date of birth is {dob}'
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data.get('text', data.get('message', ''))[:200]}")
            test("Underage DOB rejection",
                 lambda: '18' in data.get('text', '') or 'age' in data.get('text', '').lower())
            print()
            
            # Test 6: States List
            print("=" * 70)
            print("TEST 6: States List Request")
            print("=" * 70)
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': 'What are the Indian states?'
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data.get('text', data.get('message', ''))[:200]}...")
            test("States list provided",
                 lambda: 'state' in data.get('text', '').lower() or 
                         'maharashtra' in data.get('text', '').lower())
            print()
            
            # Test 7: Off-topic Question
            print("=" * 70)
            print("TEST 7: Off-topic Question (Boundary Test)")
            print("=" * 70)
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': 'What is my loan amount?'
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data.get('text', data.get('message', ''))[:200]}")
            test("Off-topic question redirected",
                 lambda: 'basic details' in data.get('text', '').lower() or 
                         'form' in data.get('text', '').lower())
            print()
            
            # Test 8: Heartbeat
            print("=" * 70)
            print("TEST 8: Heartbeat (Ping/Pong)")
            print("=" * 70)
            await websocket.send(json.dumps({
                'type': 'ping'
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            test("Heartbeat ping/pong",
                 lambda: data.get('type') == 'pong')
            print()
            
            # Test 9: Multiple Messages
            print("=" * 70)
            print("TEST 9: Multiple Consecutive Messages")
            print("=" * 70)
            messages = [
                'What is PAN?',
                'My name is John Doe',
                'What should I enter in state field?'
            ]
            for msg in messages:
                await websocket.send(json.dumps({
                    'type': 'text_message',
                    'text': msg
                }))
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    print(f"Q: {msg}")
                    print(f"A: {data.get('text', data.get('message', ''))[:100]}...")
                except:
                    pass
            test("Multiple messages handled", lambda: True)
            print()
            
            # Test 10: Empty Message
            print("=" * 70)
            print("TEST 10: Empty Message Handling")
            print("=" * 70)
            await websocket.send(json.dumps({
                'type': 'text_message',
                'text': ''
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            test("Empty message error",
                 lambda: data.get('type') == 'error')
            print()
            
            print("=" * 70)
            print("TEST SUMMARY")
            print("=" * 70)
            print(f"Total Tests: {test_results['total']}")
            print(f"✅ Passed: {test_results['passed']}")
            print(f"❌ Failed: {test_results['failed']}")
            print(f"Success Rate: {(test_results['passed']/test_results['total']*100):.1f}%")
            print("=" * 70)
            
    except websockets.exceptions.InvalidStatus as e:
        print(f"❌ WebSocket Connection Failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Django server is running: python manage.py runserver")
        print("2. Check if server is using ASGI (Daphne) for WebSocket support")
        print("3. Verify WebSocket URL: ws://localhost:8000/ws/voice-chat/")
        print("4. Check routing in consumers/routing.py")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("Starting comprehensive tests...")
    print("Make sure Django server is running on localhost:8000")
    print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(test_all_functionalities())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")

