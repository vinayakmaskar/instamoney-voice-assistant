#!/usr/bin/env python3
"""
Backend Log Analyzer for Voice Chatbot
Analyzes django.log to find patterns, issues, and performance metrics
"""

import re
import json
from datetime import datetime
from collections import defaultdict, Counter
from typing import List, Dict, Tuple

class LogAnalyzer:
    def __init__(self, log_file: str = "django.log"):
        self.log_file = log_file
        self.conversations = []
        self.function_calls = []
        self.errors = []
        self.response_times = []
        
    def parse_log(self):
        """Parse the django.log file"""
        print(f"📖 Reading log file: {self.log_file}")
        
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"❌ Log file not found: {self.log_file}")
            return
        
        print(f"📊 Total log lines: {len(lines)}")
        
        current_conversation = []
        
        for line in lines:
            # Extract user transcripts
            if "[USER TRANSCRIPT]:" in line:
                match = re.search(r'\[USER TRANSCRIPT\]:\s*(.+)', line)
                if match:
                    text = match.group(1).strip()
                    current_conversation.append({
                        'type': 'user',
                        'text': text,
                        'timestamp': self._extract_timestamp(line)
                    })
            
            # Extract bot transcripts
            elif "[BOT TRANSCRIPT]:" in line:
                match = re.search(r'\[BOT TRANSCRIPT\]:\s*(.+)', line)
                if match:
                    text = match.group(1).strip()
                    current_conversation.append({
                        'type': 'bot',
                        'text': text,
                        'timestamp': self._extract_timestamp(line)
                    })
            
            # Extract function calls
            elif "Function called:" in line:
                match = re.search(r'Function called: (\w+)\((.+)\)', line)
                if match:
                    func_name = match.group(1)
                    args = match.group(2)
                    self.function_calls.append({
                        'function': func_name,
                        'args': args,
                        'timestamp': self._extract_timestamp(line),
                        'line': line.strip()
                    })
            
            # Extract errors
            elif "ERROR" in line or "❌" in line:
                self.errors.append({
                    'timestamp': self._extract_timestamp(line),
                    'line': line.strip()
                })
        
        self.conversations = self._group_conversations(current_conversation)
        print(f"✅ Parsing complete")
    
    def _extract_timestamp(self, line: str) -> str:
        """Extract timestamp from log line"""
        match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        return match.group(1) if match else ""
    
    def _group_conversations(self, messages: List[Dict]) -> List[List[Dict]]:
        """Group messages into conversation sessions"""
        conversations = []
        current = []
        
        for msg in messages:
            if msg['text'] and msg['text'] not in ['', ' ']:
                current.append(msg)
        
        if current:
            conversations.append(current)
        
        return conversations
    
    def analyze_function_calls(self):
        """Analyze fill_form_field function calls"""
        print("\n" + "="*80)
        print("🔧 FUNCTION CALL ANALYSIS")
        print("="*80)
        
        if not self.function_calls:
            print("⚠️ No function calls found in logs")
            return
        
        print(f"\n📊 Total function calls: {len(self.function_calls)}")
        
        # Analyze by field
        field_counter = Counter()
        field_values = defaultdict(list)
        
        for call in self.function_calls:
            # Extract field and value from args
            args_match = re.search(r'field="(\w+)".*?value="([^"]*)"', call['args'])
            if args_match:
                field = args_match.group(1)
                value = args_match.group(2)
                field_counter[field] += 1
                field_values[field].append(value)
        
        print(f"\n📝 Function calls by field:")
        for field, count in field_counter.most_common():
            print(f"  - {field}: {count} times")
            print(f"    Values: {', '.join(field_values[field][:5])}")
        
        # Check for state/language confusion
        print(f"\n🔍 CRITICAL CHECKS:")
        
        state_calls = [c for c in self.function_calls if 'field="state"' in c['args']]
        lang_calls = [c for c in self.function_calls if 'field="preferredLanguage"' in c['args']]
        
        print(f"  - State field calls: {len(state_calls)}")
        print(f"  - Language field calls: {len(lang_calls)}")
        
        # Check for invalid values
        for call in self.function_calls:
            if 'field="preferredLanguage"' in call['args']:
                if 'value="en"' in call['args']:
                    print(f"    ⚠️ English language filled at: {call['timestamp']}")
            if 'field="state"' in call['args']:
                if 'value="maharashtra"' in call['args']:
                    print(f"    ✅ Maharashtra state filled at: {call['timestamp']}")
    
    def analyze_conversations(self):
        """Analyze conversation patterns"""
        print("\n" + "="*80)
        print("💬 CONVERSATION ANALYSIS")
        print("="*80)
        
        if not self.conversations or not any(self.conversations):
            print("⚠️ No conversations found in logs")
            return
        
        total_messages = sum(len(conv) for conv in self.conversations)
        print(f"\n📊 Total conversation sessions: {len(self.conversations)}")
        print(f"📊 Total messages: {total_messages}")
        
        # Analyze bot response lengths
        bot_responses = []
        for conv in self.conversations:
            for msg in conv:
                if msg['type'] == 'bot':
                    bot_responses.append(msg['text'])
        
        if bot_responses:
            print(f"\n📝 Bot response analysis:")
            print(f"  - Total bot responses: {len(bot_responses)}")
            
            word_counts = [len(resp.split()) for resp in bot_responses]
            avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
            
            print(f"  - Average response length: {avg_words:.1f} words")
            print(f"  - Longest response: {max(word_counts)} words")
            print(f"  - Shortest response: {min(word_counts)} words")
            
            # Check for verbose confirmations
            verbose_responses = [r for r in bot_responses if len(r.split()) > 5]
            print(f"  - Responses > 5 words: {len(verbose_responses)} ({len(verbose_responses)/len(bot_responses)*100:.1f}%)")
            
            if verbose_responses:
                print(f"\n  ⚠️ Sample verbose responses:")
                for resp in verbose_responses[:3]:
                    print(f"    - \"{resp}\" ({len(resp.split())} words)")
    
    def analyze_errors(self):
        """Analyze errors in logs"""
        print("\n" + "="*80)
        print("❌ ERROR ANALYSIS")
        print("="*80)
        
        if not self.errors:
            print("✅ No errors found in logs!")
            return
        
        print(f"\n📊 Total errors: {len(self.errors)}")
        
        # Group by error type
        error_types = defaultdict(int)
        for error in self.errors:
            if "WebSocket" in error['line']:
                error_types['WebSocket'] += 1
            elif "Connection" in error['line']:
                error_types['Connection'] += 1
            elif "Permission" in error['line']:
                error_types['Permission'] += 1
            else:
                error_types['Other'] += 1
        
        print(f"\n📝 Errors by type:")
        for etype, count in error_types.items():
            print(f"  - {etype}: {count}")
        
        print(f"\n🔍 Recent errors (last 5):")
        for error in self.errors[-5:]:
            print(f"  [{error['timestamp']}] {error['line'][:100]}")
    
    def find_state_language_confusion(self):
        """Specifically check for state/language confusion issue"""
        print("\n" + "="*80)
        print("🚨 STATE vs LANGUAGE CONFUSION CHECK")
        print("="*80)
        
        issues_found = []
        
        # Read log again to find context around function calls
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except FileNotFoundError:
            return
        
        for i, line in enumerate(lines):
            # Look for "Maharashtra" in user transcript
            if "[USER TRANSCRIPT]:" in line and "Maharashtra" in line.lower():
                # Check next 10 lines for function call
                for j in range(i, min(i+10, len(lines))):
                    if "Function called:" in lines[j]:
                        if 'field="preferredLanguage"' in lines[j]:
                            issues_found.append({
                                'user_input': line.strip(),
                                'function_call': lines[j].strip(),
                                'line_num': i
                            })
                        elif 'field="state"' in lines[j]:
                            print(f"✅ Correct: Maharashtra → state field (line {i})")
        
        if issues_found:
            print(f"\n❌ FOUND {len(issues_found)} STATE/LANGUAGE CONFUSION ISSUES:")
            for idx, issue in enumerate(issues_found, 1):
                print(f"\n  Issue #{idx}:")
                print(f"    User said: {issue['user_input']}")
                print(f"    Bot called: {issue['function_call']}")
                print(f"    ❌ WRONG: User mentioned Maharashtra but bot filled preferredLanguage!")
        else:
            print("\n✅ No state/language confusion found in recent logs")
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n\n" + "="*80)
        print("📊 COMPREHENSIVE LOG ANALYSIS REPORT")
        print("="*80)
        print(f"Generated: {datetime.now()}")
        
        self.parse_log()
        self.analyze_function_calls()
        self.analyze_conversations()
        self.analyze_errors()
        self.find_state_language_confusion()
        
        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE")
        print("="*80 + "\n")

def main():
    analyzer = LogAnalyzer("django.log")
    analyzer.generate_report()

if __name__ == "__main__":
    main()

