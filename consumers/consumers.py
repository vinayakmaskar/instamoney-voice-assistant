"""
Django Channels WebSocket consumers for voice chatbot.
"""
import json
import base64
import asyncio
import time
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from services.security import validate_jwt_token, check_rate_limit, sanitize_text, validate_audio_format, validate_audio_size
from services.database import create_session, close_session, save_message
from services.adk_agent import LoanAssistantAgent


class VoiceChatbotConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for voice chatbot with subprotocol authentication."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.user_id = None
        self.stage = None
        self.session_id = None
        self.agent = None
        # Real-time streaming - no buffering, send immediately
        self.receive_task = None  # Background task for receiving responses
        self.is_streaming = False
        # Auto-reconnect settings
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.is_reconnecting = False
        # Transcript accumulation buffers (for DB storage)
        self.user_transcript_buffer = []
        self.bot_transcript_buffer = []
        self.last_user_chunk_time = None
        self.last_bot_chunk_time = None
    
    async def connect(self):
        """Handle WebSocket connection with subprotocol authentication."""
        # Extract token from subprotocol
        subprotocols = self.scope.get('subprotocols', [])
        if not subprotocols:
            await self.close(code=4001, reason="No token provided")
            return
        
        token = subprotocols[0]
        
        # Validate token
        user = await validate_jwt_token(token)
        if not user:
            await self.close(code=4001, reason="Invalid or expired token")
            return
        
        # Get stage from query string
        query_string = self.scope.get('query_string', b'').decode()
        params = {}
        if query_string:
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
        
        stage = params.get('stage', 'basic_details')
        
        # Check rate limit
        if not check_rate_limit(str(user.id)):
            await self.close(code=4008, reason="Rate limit exceeded")
            return
        
        # Accept connection with subprotocol
        await self.accept(subprotocol=token)
        
        # Store user info
        self.user = user
        self.user_id = str(user.id)
        self.stage = stage
        
        # Create session
        self.session_id = await create_session(self.user_id, self.stage)
        
        # Initialize ADK Agent and start Live API session
        try:
            self.agent = LoanAssistantAgent(self.user_id, self.stage)
            
            # Start Live API session and WAIT for it to complete (prevents race condition)
            print("🔄 Starting Live API session...")
            await self._start_live_session()
            print("✅ Live API session ready!")
            
        except Exception as e:
            print(f"❌ Error initializing agent: {e}")
            import traceback
            traceback.print_exc()
            await self.close(code=4003, reason="Failed to initialize voice session")
            return
        
        # Send connection confirmation ONLY after session is ready
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Voice chatbot connected!',
            'user_id': self.user_id,
            'session_id': self.session_id,
            'stage': self.stage
        }))
    
    async def _start_live_session(self, is_reconnect=False):
        """Start Live API session and begin receiving responses."""
        try:
            # Close existing session if reconnecting
            if is_reconnect and self.agent and self.agent.live_session_context:
                try:
                    await self.agent.live_session_context.__aexit__(None, None, None)
                except:
                    pass
                self.agent.live_session = None
                self.agent.live_session_context = None
            
            await self.agent.start_live_session()
            print("✅ Live API session started" + (" (reconnected)" if is_reconnect else ""))
            
            # Reset reconnect counter on successful connection
            self.reconnect_attempts = 0
            self.is_reconnecting = False
            
            # Start background task to continuously receive responses
            self.is_streaming = True
            self.receive_task = asyncio.create_task(self._receive_responses_continuously())
            
            # Send initial greeting message from bot (only on first connect, not reconnect)
            if not is_reconnect:
                try:
                    print("🎤 Triggering initial greeting from bot...")
                    # Send a system message to trigger bot's greeting
                    await self.agent.send_text_to_live_api("start")
                except Exception as e:
                    print(f"⚠️ Could not trigger initial greeting: {e}")
            
            # Notify frontend of successful connection/reconnection
            if is_reconnect:
                await self.send(text_data=json.dumps({
                    'type': 'reconnected',
                    'message': 'Voice session reconnected successfully'
                }))
                
        except Exception as e:
            print(f"❌ Error starting Live API session: {e}")
            import traceback
            traceback.print_exc()
            
            # Notify frontend of error
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to connect to voice service. Please try again.',
                'error_code': 'SESSION_START_FAILED'
            }))
    
    async def _receive_responses_continuously(self):
        """Continuously receive audio responses from Live API in background."""
        print("🔄 Starting continuous response receiver...")
        message_count = 0
        audio_chunks_sent = 0
        
        try:
            while self.is_streaming and self.agent and self.agent.live_session:
                try:
                    # Receive with short timeout to allow checking is_streaming
                    async with asyncio.timeout(1.0):
                        async for message in self.agent.live_session.receive():
                            message_count += 1
                            audio_data = None
                            bot_text = None
                            user_text = None
                            
                            # Check for tool_call at message level
                            if hasattr(message, 'tool_call') and message.tool_call:
                                print(f"🛠️ Detected tool_call at message level: {message.tool_call}")
                                if hasattr(message.tool_call, 'function_calls'):
                                    for fc in message.tool_call.function_calls:
                                        await self._handle_tool_call(fc)
                            
                            if hasattr(message, 'server_content') and message.server_content:
                                sc = message.server_content
                                
                                # Check for user transcript (input_transcription)
                                if hasattr(sc, 'input_transcription') and sc.input_transcription:
                                    if hasattr(sc.input_transcription, 'text') and sc.input_transcription.text:
                                        user_text = str(sc.input_transcription.text)
                                        print(f"📝 [USER TRANSCRIPT]: {user_text}")  # DEBUG
                                        
                                        # Check if bot was speaking (interruption)
                                        if self.bot_transcript_buffer:
                                            await self._save_bot_turn(interrupted=True)
                                        
                                        # Accumulate user chunk
                                        self.user_transcript_buffer.append(user_text)
                                        self.last_user_chunk_time = time.time()
                                
                                # Check for bot transcript (output_transcription)
                                if hasattr(sc, 'output_transcription') and sc.output_transcription:
                                    if hasattr(sc.output_transcription, 'text') and sc.output_transcription.text:
                                        bot_text = str(sc.output_transcription.text)
                                        print(f"🤖 [BOT TRANSCRIPT]: {bot_text}")  # DEBUG
                                        
                                        # Check if user just finished speaking
                                        if self.user_transcript_buffer:
                                            await self._save_user_turn()
                                        
                                        # Accumulate bot chunk
                                        self.bot_transcript_buffer.append(bot_text)
                                        self.last_bot_chunk_time = time.time()
                                
                                # Check for turn completion
                                if hasattr(sc, 'generation_complete') and sc.generation_complete:
                                    # Save any remaining buffers
                                    if self.user_transcript_buffer:
                                        await self._save_user_turn()
                                    if self.bot_transcript_buffer:
                                        await self._save_bot_turn(interrupted=False)
                                    # Reset timing for next turn
                                    if hasattr(self, '_first_audio_time'):
                                        delattr(self, '_first_audio_time')
                                
                                # Extract audio
                                if hasattr(sc, 'model_turn') and sc.model_turn:
                                    mt = sc.model_turn
                                    if hasattr(mt, 'parts') and mt.parts:
                                        for part in mt.parts:
                                            # Check for function calls FIRST
                                            if hasattr(part, 'function_call') and part.function_call:
                                                print(f"🛠️ [DEBUG] Detected function_call in part!")  # DEBUG
                                                await self._handle_tool_call(part.function_call)
                                            
                                            # Then extract audio data
                                            if hasattr(part, 'inline_data') and part.inline_data:
                                                idata = part.inline_data
                                                if hasattr(idata, 'mime_type') and hasattr(idata, 'data'):
                                                    mime = str(idata.mime_type).lower()
                                                    if 'audio' in mime or 'pcm' in mime:
                                                        data = idata.data
                                                        if isinstance(data, bytes):
                                                            audio_data = data
                                                        else:
                                                            try:
                                                                audio_data = base64.b64decode(data)
                                                            except:
                                                                pass
                            
                            # Check interrupted event
                            if hasattr(message, 'interrupted') and message.interrupted:
                                if self.bot_transcript_buffer:
                                    await self._save_bot_turn(interrupted=True)
                            
                            # Send audio if found
                            if audio_data:
                                audio_chunks_sent += 1
                                # Log first response with timestamp
                                if audio_chunks_sent == 1 and hasattr(self, '_first_audio_time'):
                                    response_time = datetime.now()
                                    delay = (response_time - self._first_audio_time).total_seconds()
                                    print(f"⏱️  [T1] FIRST Gemini response at {response_time.strftime('%H:%M:%S.%f')[:-3]} (delay: {delay:.2f}s)")
                                try:
                                    await self.send(bytes_data=audio_data)
                                    # Log only occasionally to reduce overhead
                                    if audio_chunks_sent <= 3 or audio_chunks_sent % 20 == 0:
                                        print(f"🔊 [{audio_chunks_sent}] Sent audio: {len(audio_data)} bytes")
                                except Exception as e:
                                    print(f"❌ Failed to send audio: {e}")
                                
                except asyncio.TimeoutError:
                    # Timeout is expected - continue loop to check is_streaming
                    continue
                except Exception as e:
                    error_str = str(e).lower()
                    
                    # Check if this is a disconnection error
                    is_disconnect_error = any(err in error_str for err in [
                        'connection closed', 'no close frame', 'websocket', 
                        'connection lost', 'connection reset', 'eof'
                    ])
                    
                    if is_disconnect_error and self.is_streaming:
                        print(f"🔌 Gemini Live API disconnected: {e}")
                        
                        # Attempt auto-reconnect
                        if await self._attempt_reconnect():
                            print("✅ Reconnected successfully, continuing...")
                            continue  # Continue receiving with new session
                        else:
                            print("❌ Reconnection failed, stopping receiver")
                            break
                    elif self.is_streaming:
                        print(f"⚠️ Error in receive loop: {e}")
                        await asyncio.sleep(0.1)  # Brief pause before retry
                    else:
                        break
        except Exception as e:
            print(f"❌ Error in continuous receiver: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to reconnect if streaming should continue
            if self.is_streaming and not self.is_reconnecting:
                await self._attempt_reconnect()
        finally:
            print(f"🛑 Stopped continuous receiver: {message_count} messages, {audio_chunks_sent} audio chunks sent")
    
    
    async def _attempt_reconnect(self):
        """Attempt to reconnect to Gemini Live API."""
        if self.is_reconnecting:
            print("⏳ Already attempting reconnection...")
            return False
            
        self.is_reconnecting = True
        self.reconnect_attempts += 1
        
        print(f"🔄 Attempting reconnection ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
        
        # Notify frontend
        try:
            await self.send(text_data=json.dumps({
                'type': 'reconnecting',
                'message': f'Reconnecting to voice service... (attempt {self.reconnect_attempts})',
                'attempt': self.reconnect_attempts
            }))
        except:
            pass
        
        if self.reconnect_attempts > self.max_reconnect_attempts:
            print(f"❌ Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            self.is_reconnecting = False
            
            # Notify frontend of failure
            try:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Voice service disconnected. Please refresh the page to reconnect.',
                    'error_code': 'MAX_RECONNECTS_REACHED'
                }))
            except:
                pass
            return False
        
        try:
            # Wait before reconnecting (exponential backoff)
            wait_time = min(2 ** self.reconnect_attempts, 10)  # Max 10 seconds
            print(f"⏳ Waiting {wait_time}s before reconnecting...")
            await asyncio.sleep(wait_time)
            
            # Cancel existing receive task
            if self.receive_task and not self.receive_task.done():
                self.receive_task.cancel()
                try:
                    await self.receive_task
                except asyncio.CancelledError:
                    pass
            
            # Start new session
            await self._start_live_session(is_reconnect=True)
            return True
            
        except Exception as e:
            print(f"❌ Reconnection attempt failed: {e}")
            self.is_reconnecting = False
            
            # Notify frontend
            try:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Reconnection failed. Retrying...',
                    'error_code': 'RECONNECT_FAILED'
                }))
            except:
                pass
            
            # Retry recursively
            return await self._attempt_reconnect()
    
    async def _save_user_turn(self):
        """Concatenate user transcript chunks and save to database."""
        if not self.user_transcript_buffer:
            return
        
        complete_transcript = ''.join(self.user_transcript_buffer).strip()
        if complete_transcript:
            await save_message(
                self.user_id, 
                self.stage, 
                self.session_id, 
                'user', 
                complete_transcript, 
                'text',
                metadata={'complete': True}
            )
        
        # Clear buffer
        self.user_transcript_buffer = []
        self.last_user_chunk_time = None
    
    async def _save_bot_turn(self, interrupted=False):
        """Concatenate bot transcript chunks and save to database."""
        if not self.bot_transcript_buffer:
            return
        
        complete_transcript = ''.join(self.bot_transcript_buffer).strip()
        if complete_transcript:
            await save_message(
                self.user_id, 
                self.stage, 
                self.session_id, 
                'assistant', 
                complete_transcript, 
                'text',
                metadata={'interrupted': interrupted, 'complete': not interrupted}
            )
        
        # Clear buffer
        self.bot_transcript_buffer = []
        self.last_bot_chunk_time = None
    
    async def _extract_form_data_from_transcript(self, transcript: str):
        """
        Extract structured form data from Gemini's transcript output.
        Looks for pattern: FORM_DATA: {"field": "fieldName", "value": "extractedValue"}
        """
        import re
        import json
        
        # Look for FORM_DATA: {...} pattern
        pattern = r'FORM_DATA:\s*(\{[^}]+\})'
        matches = re.findall(pattern, transcript)
        
        for match in matches:
            try:
                # Parse JSON
                data = json.loads(match)
                field = data.get('field')
                value = data.get('value')
                
                if not field or not value:
                    continue
                
                print(f"✅ Extracted from transcript: {field} = {value}")
                
                # Map field names to frontend expectations
                field_mapping = {
                    'fullName': 'fullName',
                    'panNumber': 'panNumber',
                    'dateOfBirth': 'dateOfBirth',
                    'state': 'state',
                    'preferredLanguage': 'preferredLanguage'
                }
                
                mapped_field = field_mapping.get(field, field)
                display_value = value
                
                # Send to frontend
                await self.send(text_data=json.dumps({
                    'type': 'form_suggestion',
                    'field': mapped_field,
                    'value': value,
                    'display_value': display_value,
                    'confidence': 'high',
                    'timestamp': datetime.now().isoformat()
                }))
                
                # Save to database
                await save_message(
                    self.user_id,
                    self.stage,
                    self.session_id,
                    'system',
                    f"Auto-filled {mapped_field}: {display_value}",
                    'text',
                    metadata={'type': 'form_autofill', 'field': mapped_field, 'value': value, 'confidence': 'high'}
                )
                
                print(f"📤 Sent form_suggestion to frontend: {mapped_field} = {display_value}")
                
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to parse FORM_DATA JSON: {match} - Error: {e}")
            except Exception as e:
                print(f"❌ Error extracting form data: {e}")
    
    async def _handle_tool_call(self, function_call):
        """
        Handle function call from Gemini and send response back using LiveClientToolResponse.
        Uses send(input=LiveClientToolResponse(...)) instead of send_tool_response().
        """
        func_name = function_call.name
        func_id = function_call.id  # CRITICAL: Need the ID from the function call
        args = dict(function_call.args)
        
        print(f"📞 Function called: {func_name} (id: {func_id}) with args: {args}")
        
        if func_name == "fill_form_field":
            field = args.get('field_name')
            value = args.get('value')
            display = args.get('display_value', value)
            confidence = args.get('confidence', 'high')
            
            # ✅ VALIDATION: Check format and script
            validation_success = True
            validation_error = None
            
            # Validate date format (must be YYYY-MM-DD)
            if field == 'dateOfBirth':
                import re
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                    validation_success = False
                    validation_error = f"Invalid date format: {value}. Must be YYYY-MM-DD"
                    print(f"⚠️ {validation_error}")
            
            # Validate Latin script (no Devanagari, Tamil, etc. in value)
            if field in ['fullName', 'panNumber']:
                # Check if value contains non-Latin characters
                import unicodedata
                has_non_latin = any(
                    unicodedata.category(char) not in ['Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nd', 'Zs', 'Pd', 'Pc']
                    and not char.isascii()
                    for char in value
                )
                if has_non_latin:
                    validation_success = False
                    validation_error = f"Non-Latin script detected in {field}: {value}"
                    print(f"⚠️ {validation_error}")
            
            print(f"✅ Extracted: {field} = {display} (confidence: {confidence}) [validation: {validation_success}]")
            
            # Send to frontend for auto-fill (even if validation fails, let frontend decide)
            await self.send(text_data=json.dumps({
                'type': 'form_suggestion',
                'field': field,
                'value': value,
                'display_value': display,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }))
            
            # Save to database
            await save_message(
                self.user_id,
                self.stage,
                self.session_id,
                'system',
                f"Auto-filled {field}: {display}",
                'text',
                metadata={
                    'type': 'form_autofill',
                    'field': field,
                    'value': value,
                    'confidence': confidence,
                    'validation': 'success' if validation_success else 'failed',
                    'validation_error': validation_error
                }
            )
            
            # CRITICAL: Send function response back using LiveClientToolResponse wrapper
            import google.genai.types as types
            
            try:
                # Prepare response based on validation
                if validation_success:
                    response_data = {"success": True, "field": field, "value": value}
                else:
                    response_data = {
                        "success": False,
                        "field": field,
                        "value": value,
                        "error": validation_error
                    }
                
                # NEW APPROACH: Wrap FunctionResponse in LiveClientToolResponse
                await self.agent.live_session.send(
                    input=types.LiveClientToolResponse(
                        function_responses=[
                            types.FunctionResponse(
                                id=func_id,  # Must include the ID from the function call
                                name=func_name,
                                response=response_data
                            )
                        ]
                    )
                )
                print(f"📤 Sent function response back to Gemini: {response_data}")
            except Exception as e:
                print(f"❌ Error sending function response: {e}")
                import traceback
                traceback.print_exc()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Save any remaining transcripts before disconnect
        await self._save_user_turn()
        await self._save_bot_turn()
        
        # Stop streaming
        self.is_streaming = False
        
        # Cancel receive task
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
        
        # Close Live API session
        if self.agent and self.agent.live_session:
            try:
                if self.agent.live_session_context:
                    await self.agent.live_session_context.__aexit__(None, None, None)
            except:
                pass
        
        # Close session
        if self.session_id:
            await close_session(self.session_id)
        
        # Cleanup agent
        if self.agent:
            # Agent cleanup if needed
            pass
        
        print(f"User {self.user_id} disconnected. Code: {close_code}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        try:
            if text_data:
                await self.handle_text_message(text_data)
            elif bytes_data:
                # Log first chunk with timestamp
                if not hasattr(self, '_first_audio_time'):
                    self._first_audio_time = datetime.now()
                    print(f"⏱️  [T0] FIRST audio from user at {self._first_audio_time.strftime('%H:%M:%S.%f')[:-3]}")
                await self.handle_audio_data(bytes_data)
            else:
                print("⚠️ Received empty message")
        except Exception as e:
            print(f"❌ Error in receive: {e}")
            import traceback
            traceback.print_exc()
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'An error occurred processing your message'
            }))
    
    async def handle_text_message(self, text_data: str):
        """Process text messages through agent and Live API."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'text_message':
                user_text = data.get('text', '')
                
                # Sanitize input
                user_text = sanitize_text(user_text)
                
                if not user_text:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Empty message'
                    }))
                    return
                
                # Check if agent needs tools
                agent_result = await self.agent.process_with_agent(user_text)
                
                if agent_result.get('needs_tools'):
                    # Agent used tools - send tool results
                    await self.send(text_data=json.dumps({
                        'type': 'tool_result',
                        'text': agent_result.get('text', ''),
                        'tool_calls': agent_result.get('tool_calls', []),
                        'timestamp': datetime.now().isoformat()
                    }))
                    
                    # Handle tool results (validation, suggestions, etc.)
                    for tool_call in agent_result.get('tool_calls', []):
                        tool_name = tool_call.get('name') if isinstance(tool_call, dict) else None
                        
                        if tool_name == 'suggest_form_field':
                            # Form field suggestion
                            await self.send(text_data=json.dumps({
                                'type': 'form_suggestion',
                                'field': tool_call.get('args', {}).get('field_name'),
                                'value': tool_call.get('args', {}).get('value'),
                                'timestamp': datetime.now().isoformat()
                            }))
                        elif tool_name in ['validate_pan', 'validate_dob']:
                            # Validation results - send validation status
                            tool_result = tool_call.get('result', {})
                            await self.send(text_data=json.dumps({
                                'type': 'validation_result',
                                'tool': tool_name,
                                'valid': tool_result.get('valid', False),
                                'message': tool_result.get('message', ''),
                                'suggestion': tool_result.get('suggestion', ''),
                                'timestamp': datetime.now().isoformat()
                            }))
                            
                            # If validation passes, suggest form field
                            if tool_result.get('valid'):
                                if tool_name == 'validate_pan':
                                    await self.send(text_data=json.dumps({
                                        'type': 'form_suggestion',
                                        'field': 'panNumber',
                                        'value': tool_result.get('pan', ''),
                                        'timestamp': datetime.now().isoformat()
                                    }))
                                elif tool_name == 'validate_dob':
                                    await self.send(text_data=json.dumps({
                                        'type': 'form_suggestion',
                                        'field': 'dateOfBirth',
                                        'value': tool_result.get('formatted_date', ''),
                                        'timestamp': datetime.now().isoformat()
                                    }))
                        elif tool_name == 'get_indian_states':
                            # States list - already included in agent response text
                            pass
                    
                    # Save messages
                    await save_message(self.user_id, self.stage, self.session_id, 'user', user_text, 'text')
                    await save_message(self.user_id, self.stage, self.session_id, 'assistant', agent_result.get('text', ''), 'text')
                else:
                    # Stream response using Live API
                    full_response = ""
                    async for chunk in self.agent.stream_live_response(user_text):
                        full_response += chunk
                        await self.send(text_data=json.dumps({
                            'type': 'response_text',
                            'text': chunk,
                            'timestamp': datetime.now().isoformat(),
                            'is_final': False
                        }))
                    
                    # Send final message
                    if full_response:
                        await self.send(text_data=json.dumps({
                            'type': 'response_text',
                            'text': '',
                            'timestamp': datetime.now().isoformat(),
                            'is_final': True
                        }))
                        
                        # Save messages
                        await save_message(self.user_id, self.stage, self.session_id, 'user', user_text, 'text')
                        await save_message(self.user_id, self.stage, self.session_id, 'assistant', full_response, 'text')
            
            elif message_type == 'ping':
                # Heartbeat
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            print(f"Error handling text message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing message: {str(e)}'
            }))
    
    async def handle_audio_data(self, bytes_data: bytes):
        """
        Send audio chunks immediately to Live API for real-time processing.
        No buffering - true real-time streaming.
        """
        try:
            # Skip if reconnecting
            if self.is_reconnecting:
                return
            
            # Validate audio size
            if not validate_audio_size(len(bytes_data)):
                print(f"❌ Audio chunk too large: {len(bytes_data)} bytes")
                return
            
            # Ensure Live API session is ready
            if not self.agent or not self.agent.live_session:
                if not self.is_reconnecting:
                    print("⚠️ Live API session not ready, triggering reconnect...")
                    asyncio.create_task(self._attempt_reconnect())
                return
            
            # Send immediately to Live API (no buffering)
            await self.agent.send_audio_realtime(bytes_data)
        
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if this is a disconnection error
            is_disconnect_error = any(err in error_str for err in [
                'connection closed', 'no close frame', 'websocket', 
                'connection lost', 'connection reset', 'eof'
            ])
            
            if is_disconnect_error:
                print(f"🔌 Send failed - Gemini disconnected: {e}")
                if not self.is_reconnecting:
                    asyncio.create_task(self._attempt_reconnect())
            else:
                print(f"❌ Error sending audio: {e}")

