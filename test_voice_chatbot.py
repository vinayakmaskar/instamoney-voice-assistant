#!/usr/bin/env python3
"""
Comprehensive Voice Chatbot Test Suite
Tests all real-time scenarios, edge cases, and form filling functionality
"""

import asyncio
import websockets
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import sys

class VoiceChatbotTester:
    def __init__(self, ws_url: str = "ws://localhost:8000/ws/voice-chat/?stage=basic_details"):
        self.ws_url = ws_url
        self.ws = None
        self.test_results = []
        self.form_data = {}
        self.current_test = None
        
    async def connect(self):
        """Connect to WebSocket"""
        try:
            self.ws = await websockets.connect(self.ws_url)
            print("✅ Connected to WebSocket")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.ws:
            await self.ws.close()
            print("🔌 Disconnected")
    
    async def send_message(self, message: str, message_type: str = "text"):
        """Send a message to the bot"""
        data = {
            "type": message_type,
            "text": message
        }
        await self.ws.send(json.dumps(data))
        print(f"\n👤 USER: {message}")
    
    async def receive_messages(self, timeout: float = 5.0) -> List[Dict]:
        """Receive messages from bot with timeout"""
        messages = []
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                    data = json.loads(message)
                    messages.append(data)
                    
                    if data.get('type') == 'transcript':
                        print(f"🤖 BOT: {data.get('text', '')}")
                    elif data.get('type') == 'form_suggestion':
                        field = data.get('field')
                        value = data.get('value')
                        self.form_data[field] = value
                        print(f"📝 FORM UPDATE: {field} = {value}")
                    elif data.get('type') == 'error':
                        print(f"❌ ERROR: {data.get('message', '')}")
                        
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("⚠️ Connection closed by server")
                    break
        except Exception as e:
            print(f"⚠️ Error receiving messages: {e}")
        
        return messages
    
    async def test_scenario(self, name: str, user_input: str, expected_behavior: str, 
                           expected_field: Optional[str] = None, 
                           expected_value: Optional[str] = None):
        """Test a single scenario"""
        print("\n" + "="*80)
        print(f"🧪 TEST: {name}")
        print(f"📋 Expected: {expected_behavior}")
        print("="*80)
        
        self.current_test = {
            'name': name,
            'user_input': user_input,
            'expected_behavior': expected_behavior,
            'expected_field': expected_field,
            'expected_value': expected_value,
            'timestamp': datetime.now().isoformat(),
            'passed': False,
            'bot_response': None,
            'form_updates': {},
            'issues': []
        }
        
        # Clear form data for this test
        old_form_data = self.form_data.copy()
        
        # Send message
        await self.send_message(user_input)
        
        # Receive responses
        messages = await self.receive_messages(timeout=8.0)
        
        # Analyze results
        bot_transcripts = [m.get('text', '') for m in messages if m.get('type') == 'transcript']
        form_updates = {m.get('field'): m.get('value') for m in messages if m.get('type') == 'form_suggestion'}
        
        self.current_test['bot_response'] = ' '.join(bot_transcripts) if bot_transcripts else "NO RESPONSE"
        self.current_test['form_updates'] = form_updates
        
        # Check if expected field was updated
        if expected_field:
            if expected_field in form_updates:
                actual_value = form_updates[expected_field]
                if expected_value and actual_value == expected_value:
                    self.current_test['passed'] = True
                    print(f"✅ PASS: Field '{expected_field}' correctly filled with '{actual_value}'")
                elif expected_value and actual_value != expected_value:
                    self.current_test['issues'].append(f"Field '{expected_field}' has wrong value: {actual_value} (expected: {expected_value})")
                    print(f"❌ FAIL: Field '{expected_field}' has wrong value: {actual_value} (expected: {expected_value})")
                else:
                    self.current_test['passed'] = True
                    print(f"✅ PASS: Field '{expected_field}' was filled")
            else:
                self.current_test['issues'].append(f"Field '{expected_field}' was not filled")
                print(f"❌ FAIL: Field '{expected_field}' was not filled")
        else:
            # No field expected to be filled (e.g., questions)
            if bot_transcripts:
                self.current_test['passed'] = True
                print(f"✅ PASS: Bot responded appropriately")
            else:
                self.current_test['issues'].append("Bot did not respond")
                print(f"❌ FAIL: Bot did not respond")
        
        self.test_results.append(self.current_test)
        await asyncio.sleep(1)  # Brief pause between tests
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("\n" + "🚀 STARTING COMPREHENSIVE VOICE CHATBOT TEST SUITE" + "\n")
        print(f"Timestamp: {datetime.now()}")
        print(f"WebSocket URL: {self.ws_url}")
        
        if not await self.connect():
            print("❌ Cannot proceed - connection failed")
            return
        
        try:
            # ============================================================================
            # CATEGORY 1: BASIC FORM FILLING (Happy Path)
            # ============================================================================
            print("\n\n" + "🟢 CATEGORY 1: BASIC FORM FILLING (HAPPY PATH)" + "\n")
            
            await self.test_scenario(
                name="Fill Full Name (English)",
                user_input="My name is Vinayak Masker",
                expected_behavior="Bot should fill fullName field and give brief confirmation",
                expected_field="fullName",
                expected_value="Vinayak Masker"
            )
            
            await self.test_scenario(
                name="Fill PAN Number",
                user_input="My PAN number is ABCDE1234F",
                expected_behavior="Bot should fill panNumber field",
                expected_field="panNumber",
                expected_value="ABCDE1234F"
            )
            
            await self.test_scenario(
                name="Fill Date of Birth",
                user_input="My date of birth is 26th April 2002",
                expected_behavior="Bot should fill dateOfBirth in YYYY-MM-DD format",
                expected_field="dateOfBirth",
                expected_value="2002-04-26"
            )
            
            await self.test_scenario(
                name="Fill State (English)",
                user_input="I live in Maharashtra",
                expected_behavior="Bot should fill state as 'maharashtra' (snake_case)",
                expected_field="state",
                expected_value="maharashtra"
            )
            
            await self.test_scenario(
                name="Fill Preferred Language",
                user_input="I prefer English language",
                expected_behavior="Bot should fill preferredLanguage as 'en'",
                expected_field="preferredLanguage",
                expected_value="en"
            )
            
            # ============================================================================
            # CATEGORY 2: MULTILINGUAL INPUT
            # ============================================================================
            print("\n\n" + "🌍 CATEGORY 2: MULTILINGUAL INPUT" + "\n")
            
            await self.test_scenario(
                name="Marathi Name Input",
                user_input="माझे नाव विनायक मास्कर आहे",
                expected_behavior="Bot should understand and fill fullName",
                expected_field="fullName"
            )
            
            await self.test_scenario(
                name="Hindi State Input",
                user_input="मैं महाराष्ट्र में रहता हूं",
                expected_behavior="Bot should fill state as 'maharashtra'",
                expected_field="state",
                expected_value="maharashtra"
            )
            
            await self.test_scenario(
                name="Marathi Language Preference",
                user_input="मला मराठी भाषा आवडते",
                expected_behavior="Bot should fill preferredLanguage as 'mr'",
                expected_field="preferredLanguage",
                expected_value="mr"
            )
            
            # ============================================================================
            # CATEGORY 3: EDGE CASES - INVALID DATA
            # ============================================================================
            print("\n\n" + "⚠️ CATEGORY 3: EDGE CASES - INVALID DATA" + "\n")
            
            await self.test_scenario(
                name="Invalid State Name",
                user_input="I live in Atlantis",
                expected_behavior="Bot should say state not available and ask again",
                expected_field=None  # Should NOT fill
            )
            
            await self.test_scenario(
                name="Unsupported Language",
                user_input="I prefer French language",
                expected_behavior="Bot should say language not available and ask again",
                expected_field=None  # Should NOT fill
            )
            
            await self.test_scenario(
                name="Invalid PAN Format (too short)",
                user_input="My PAN is ABC123",
                expected_behavior="Bot should ask for correct PAN format",
                expected_field=None  # Should NOT fill invalid PAN
            )
            
            await self.test_scenario(
                name="Invalid Date Format",
                user_input="My date of birth is next Tuesday",
                expected_behavior="Bot should ask for proper date",
                expected_field=None
            )
            
            # ============================================================================
            # CATEGORY 4: QUESTIONS & EXPLANATIONS
            # ============================================================================
            print("\n\n" + "❓ CATEGORY 4: QUESTIONS & EXPLANATIONS" + "\n")
            
            await self.test_scenario(
                name="What is PAN?",
                user_input="What is PAN number?",
                expected_behavior="Bot should explain what PAN is (detailed explanation)",
                expected_field=None
            )
            
            await self.test_scenario(
                name="PAN Format Question",
                user_input="What is the format of PAN number?",
                expected_behavior="Bot should explain PAN format",
                expected_field=None
            )
            
            await self.test_scenario(
                name="Available Languages Question",
                user_input="Which languages are available?",
                expected_behavior="Bot should list all 12 supported languages",
                expected_field=None
            )
            
            await self.test_scenario(
                name="State List Question",
                user_input="Which states can I choose?",
                expected_behavior="Bot should give examples of Indian states",
                expected_field=None
            )
            
            # ============================================================================
            # CATEGORY 5: UPDATE REQUESTS (Should Ask for Value)
            # ============================================================================
            print("\n\n" + "🔄 CATEGORY 5: UPDATE REQUESTS" + "\n")
            
            await self.test_scenario(
                name="Request to Update PAN (No Value)",
                user_input="I want to update my PAN number",
                expected_behavior="Bot should ASK what the new PAN is (NOT auto-fill)",
                expected_field=None  # Should NOT fill without value
            )
            
            await self.test_scenario(
                name="Request to Update Name (No Value)",
                user_input="I want to change my name",
                expected_behavior="Bot should ASK what the new name is",
                expected_field=None
            )
            
            await self.test_scenario(
                name="Update PAN with Value",
                user_input="I want to update my PAN to XYZAB9876C",
                expected_behavior="Bot should fill panNumber with new value",
                expected_field="panNumber",
                expected_value="XYZAB9876C"
            )
            
            # ============================================================================
            # CATEGORY 6: MULTIPLE DATA POINTS AT ONCE
            # ============================================================================
            print("\n\n" + "📦 CATEGORY 6: MULTIPLE DATA POINTS" + "\n")
            
            await self.test_scenario(
                name="Name and State Together",
                user_input="My name is Raj Sharma and I live in Karnataka",
                expected_behavior="Bot should fill BOTH fullName and state (or ask to provide one by one)",
                expected_field="fullName"  # At least one should fill
            )
            
            # ============================================================================
            # CATEGORY 7: CORRECTIONS & CHANGES
            # ============================================================================
            print("\n\n" + "✏️ CATEGORY 7: CORRECTIONS & CHANGES" + "\n")
            
            await self.test_scenario(
                name="Correct Previous Entry",
                user_input="Actually, my PAN is PQRST5678U",
                expected_behavior="Bot should update PAN to new value",
                expected_field="panNumber",
                expected_value="PQRST5678U"
            )
            
            await self.test_scenario(
                name="Change State",
                user_input="Sorry, I meant Tamil Nadu",
                expected_behavior="Bot should update state to tamil_nadu",
                expected_field="state",
                expected_value="tamil_nadu"
            )
            
            # ============================================================================
            # CATEGORY 8: PARTIAL / INCOMPLETE INPUT
            # ============================================================================
            print("\n\n" + "⚡ CATEGORY 8: PARTIAL / INCOMPLETE INPUT" + "\n")
            
            await self.test_scenario(
                name="Just Field Name (No Value)",
                user_input="Full name",
                expected_behavior="Bot should ASK for the full name value",
                expected_field=None
            )
            
            await self.test_scenario(
                name="Just Value (Context-Dependent)",
                user_input="ABCDE1234F",
                expected_behavior="Bot should ask which field this is for (or infer from context)",
                expected_field=None
            )
            
            # ============================================================================
            # CATEGORY 9: CONFUSION SCENARIOS (Known Issues)
            # ============================================================================
            print("\n\n" + "🔍 CATEGORY 9: CONFUSION SCENARIOS (CRITICAL)" + "\n")
            
            await self.test_scenario(
                name="State Mention in English (Should Fill State, NOT Language)",
                user_input="My state is Maharashtra",
                expected_behavior="Bot should fill STATE field (not preferredLanguage)",
                expected_field="state",
                expected_value="maharashtra"
            )
            
            await self.test_scenario(
                name="Explicit State Update",
                user_input="Can you please update my state to Maharashtra",
                expected_behavior="Bot should fill state field (not preferredLanguage)",
                expected_field="state",
                expected_value="maharashtra"
            )
            
            # ============================================================================
            # CATEGORY 10: BRIEF CONFIRMATION CHECK
            # ============================================================================
            print("\n\n" + "✅ CATEGORY 10: CONFIRMATION BREVITY" + "\n")
            
            test_before_fill = len(self.test_results)
            await self.test_scenario(
                name="Check Confirmation is Brief",
                user_input="My name is Test User",
                expected_behavior="Bot confirmation should be ≤5 words (e.g., 'Done', 'Filled')",
                expected_field="fullName",
                expected_value="Test User"
            )
            # Check word count of response
            if self.test_results[-1]['bot_response']:
                word_count = len(self.test_results[-1]['bot_response'].split())
                if word_count > 5:
                    self.test_results[-1]['issues'].append(f"Response too long: {word_count} words (should be ≤5)")
                    self.test_results[-1]['passed'] = False
            
        except Exception as e:
            print(f"\n❌ Test suite error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.disconnect()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n\n" + "="*80)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  ✅ Passed: {passed_tests}")
        print(f"  ❌ Failed: {failed_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for i, test in enumerate(self.test_results):
                if not test['passed']:
                    print(f"\n  {i+1}. {test['name']}")
                    print(f"     User Input: {test['user_input']}")
                    print(f"     Bot Response: {test['bot_response']}")
                    print(f"     Expected: {test['expected_behavior']}")
                    print(f"     Issues: {', '.join(test['issues'])}")
        
        print(f"\n📝 CURRENT FORM STATE:")
        print(f"  {json.dumps(self.form_data, indent=2)}")
        
        # Save detailed report to file
        report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump({
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'success_rate': passed_tests/total_tests*100
                },
                'tests': self.test_results,
                'final_form_state': self.form_data
            }, f, indent=2)
        
        print(f"\n💾 Detailed report saved: {report_filename}")
        
        print("\n" + "="*80 + "\n")

async def main():
    """Run the test suite"""
    tester = VoiceChatbotTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Test suite interrupted by user")
        sys.exit(0)

