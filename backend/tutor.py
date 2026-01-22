# English Tutor - Direct Groq Integration with API Key Rotation
import json
import os
import threading
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class APIKeyRotator:
    """Manages rotation of multiple Groq API keys"""

    def __init__(self):
        self.keys = []
        self.current_index = 0
        self.lock = threading.Lock()
        self.error_counts = {}
        self.max_errors = 3  # Max consecutive errors before skipping a key

        # Load API keys from environment
        # GROQ_API_KEY_1, GROQ_API_KEY_2, GROQ_API_KEY_3
        for i in range(1, 4):
            key = os.getenv(f'GROQ_API_KEY_{i}', '')
            if key:
                self.keys.append(key)
                self.error_counts[i - 1] = 0

        # Fallback to single GROQ_API_KEY if no numbered keys
        if not self.keys:
            single_key = os.getenv('GROQ_API_KEY', '')
            if single_key:
                self.keys.append(single_key)
                self.error_counts[0] = 0

        print(f"API Key Rotator initialized with {len(self.keys)} key(s)")

    def get_current_key(self) -> str:
        """Get the current API key"""
        if not self.keys:
            return ''

        with self.lock:
            return self.keys[self.current_index]

    def rotate_key(self, had_error: bool = False):
        """Rotate to the next API key"""
        if len(self.keys) <= 1:
            return

        with self.lock:
            if had_error:
                self.error_counts[self.current_index] += 1
            else:
                # Reset error count on success
                self.error_counts[self.current_index] = 0

            # Find next available key
            attempts = 0
            while attempts < len(self.keys):
                self.current_index = (self.current_index + 1) % len(self.keys)

                # Skip keys with too many errors
                if self.error_counts[self.current_index] < self.max_errors:
                    break
                attempts += 1

            # If all keys have errors, reset error counts and use first key
            if attempts >= len(self.keys):
                for i in range(len(self.keys)):
                    self.error_counts[i] = 0
                self.current_index = 0

            print(f"Rotated to API key {self.current_index + 1}")

    def get_client(self) -> Groq:
        """Get a Groq client with current key"""
        return Groq(api_key=self.get_current_key())

    def get_key_count(self) -> int:
        """Return number of available keys"""
        return len(self.keys)


# Global API key rotator instance
api_rotator = APIKeyRotator()

# Tutor mode - instant corrections
TUTOR_SYSTEM_PROMPT = """You are an expert English language tutor. Your role is to:
1. Help users improve their English speaking and writing skills
2. Correct grammar mistakes gently and explain why
3. Suggest better vocabulary and expressions
4. Encourage the user and make learning enjoyable
5. Adapt to the user's proficiency level

Always be patient, supportive, and provide clear explanations.
Keep responses conversational and not too long."""

# Chat mode - natural conversation like a friend
CHAT_SYSTEM_PROMPT = """You are a friendly English-speaking conversation partner. Your role is to:
1. Have natural, casual conversations like a native English speaker
2. Talk about any topic the user wants - hobbies, news, life, etc.
3. Be friendly, warm, and engaging
4. Ask follow-up questions to keep the conversation going
5. DO NOT correct grammar or mention language learning

Act like a normal friend chatting, not a teacher. Keep responses natural and conversational."""

GRAMMAR_CHECK_PROMPT = """Analyze the following text for grammar errors.
For each error found, provide the original text, the correction, and a brief explanation.

Text: {user_message}

Respond ONLY with valid JSON in this exact format (no other text):
{{
    "errors": [
        {{
            "original": "the incorrect phrase",
            "corrected": "the correct phrase",
            "explanation": "brief explanation"
        }}
    ],
    "is_correct": true or false
}}

If there are no errors, return: {{"errors": [], "is_correct": true}}"""

SESSION_FEEDBACK_PROMPT = """Analyze the following conversation messages from an English learner and provide comprehensive feedback.

User messages:
{user_messages}

Provide detailed feedback in the following JSON format:
{{
    "overall_score": 1-10,
    "grammar_errors": [
        {{
            "original": "what they said",
            "corrected": "correct version",
            "explanation": "why this is wrong",
            "message_number": 1
        }}
    ],
    "vocabulary_suggestions": [
        {{
            "original": "basic word/phrase used",
            "better_alternatives": ["better option 1", "better option 2"],
            "context": "when to use these"
        }}
    ],
    "strengths": ["list of things they did well"],
    "areas_to_improve": ["specific areas to work on"],
    "tips": ["actionable tips for improvement"],
    "encouragement": "a positive, encouraging message"
}}

Be thorough but constructive. Focus on patterns, not just individual errors."""


class EnglishTutor:
    def __init__(self):
        self.rotator = api_rotator
        self.model = os.getenv('MODEL_NAME', 'llama-3.3-70b-versatile')
        self.conversation_history = []
        self.user_messages_log = []  # Store user messages for chat mode feedback
        self.max_history = 20
        self.mode = 'tutor'  # 'tutor' or 'chat'

    def _make_api_call(self, messages, temperature=0.7, max_tokens=500):
        """Make API call with automatic retry and key rotation"""
        max_retries = self.rotator.get_key_count()
        last_error = None

        for attempt in range(max_retries):
            try:
                client = self.rotator.get_client()
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                # Success - rotate for next request (load balancing)
                if attempt == 0:
                    self.rotator.rotate_key(had_error=False)
                return response
            except Exception as e:
                last_error = e
                print(f"API call failed with key {self.rotator.current_index + 1}: {e}")
                self.rotator.rotate_key(had_error=True)

        raise last_error if last_error else Exception("All API keys failed")

    def set_mode(self, mode: str):
        """Set the conversation mode"""
        if mode in ['tutor', 'chat']:
            self.mode = mode
            # Clear history when switching modes
            self.conversation_history = []
            self.user_messages_log = []

    def check_grammar(self, user_message: str) -> list:
        """Check grammar and return corrections"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a grammar checker. Respond ONLY with valid JSON, no other text."
                },
                {
                    "role": "user",
                    "content": GRAMMAR_CHECK_PROMPT.format(user_message=user_message)
                }
            ]
            response = self._make_api_call(messages, temperature=0.3, max_tokens=500)

            result_text = response.choices[0].message.content.strip()

            try:
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = result_text[start_idx:end_idx]
                    result = json.loads(json_str)
                    return result.get('errors', [])
            except json.JSONDecodeError:
                pass

        except Exception as e:
            print(f"Grammar check error: {e}")

        return []

    def generate_tutor_response(self, user_message: str, corrections: list) -> str:
        """Generate tutor response with corrections"""
        messages = [{"role": "system", "content": TUTOR_SYSTEM_PROMPT}]

        for msg in self.conversation_history[-10:]:
            messages.append(msg)

        if corrections:
            correction_text = "\n".join([
                f"- '{err.get('original', '')}' should be '{err.get('corrected', '')}'"
                for err in corrections
            ])
            prompt = f"""The user said: "{user_message}"

I found these grammar issues:
{correction_text}

Please respond naturally as a tutor - acknowledge what they said, gently mention the corrections with brief explanations, and continue the conversation. Keep it friendly and encouraging."""
        else:
            prompt = f"""The user said: "{user_message}"

Their grammar is correct! Respond naturally as a tutor - continue the conversation and maybe ask a follow-up question to keep them practicing."""

        messages.append({"role": "user", "content": prompt})

        try:
            response = self._make_api_call(messages, temperature=0.7, max_tokens=500)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Response generation error: {e}")
            return "I'm sorry, I encountered an error. Please try again."

    def generate_chat_response(self, user_message: str) -> str:
        """Generate natural chat response without corrections"""
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]

        for msg in self.conversation_history[-10:]:
            messages.append(msg)

        messages.append({"role": "user", "content": user_message})

        try:
            response = self._make_api_call(messages, temperature=0.8, max_tokens=500)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Response generation error: {e}")
            return "I'm sorry, I encountered an error. Please try again."

    def process_message(self, user_message: str) -> dict:
        """Process a user message based on current mode"""
        # Add to history
        self.conversation_history.append({"role": "user", "content": user_message})

        if self.mode == 'tutor':
            # Tutor mode: check grammar and provide corrections
            corrections = self.check_grammar(user_message)
            ai_response = self.generate_tutor_response(user_message, corrections)
            tips = [err.get('explanation', '') for err in corrections[:3] if err.get('explanation')]

            result = {
                'message': ai_response,
                'corrections': corrections,
                'feedback': {
                    'tips': tips,
                    'encouragement': 'Keep practicing!' if not corrections else 'Good effort!'
                },
                'mode': 'tutor'
            }
        else:
            # Chat mode: natural conversation, log for later feedback
            self.user_messages_log.append(user_message)
            ai_response = self.generate_chat_response(user_message)

            result = {
                'message': ai_response,
                'corrections': [],
                'feedback': {},
                'mode': 'chat',
                'messages_count': len(self.user_messages_log)
            }

        # Add AI response to history
        self.conversation_history.append({"role": "assistant", "content": ai_response})

        # Trim history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        return result

    def get_session_feedback(self) -> dict:
        """Get comprehensive feedback for chat mode session"""
        if not self.user_messages_log:
            return {
                'error': 'No messages to analyze',
                'overall_score': 0,
                'grammar_errors': [],
                'vocabulary_suggestions': [],
                'strengths': [],
                'areas_to_improve': [],
                'tips': [],
                'encouragement': 'Start chatting to get feedback!'
            }

        # Format user messages for analysis
        user_messages_text = "\n".join([
            f"{i+1}. \"{msg}\""
            for i, msg in enumerate(self.user_messages_log)
        ])

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert English language analyst. Provide detailed, constructive feedback. Respond ONLY with valid JSON."
                },
                {
                    "role": "user",
                    "content": SESSION_FEEDBACK_PROMPT.format(user_messages=user_messages_text)
                }
            ]
            response = self._make_api_call(messages, temperature=0.5, max_tokens=1500)

            result_text = response.choices[0].message.content.strip()

            # Parse JSON
            try:
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = result_text[start_idx:end_idx]
                    feedback = json.loads(json_str)
                    feedback['total_messages'] = len(self.user_messages_log)
                    feedback['user_messages'] = self.user_messages_log
                    return feedback
            except json.JSONDecodeError:
                pass

        except Exception as e:
            print(f"Session feedback error: {e}")

        return {
            'error': 'Could not generate feedback',
            'overall_score': 0,
            'grammar_errors': [],
            'vocabulary_suggestions': [],
            'strengths': [],
            'areas_to_improve': [],
            'tips': [],
            'encouragement': 'Please try again!'
        }

    def clear_history(self):
        """Clear conversation history and logs"""
        self.conversation_history = []
        self.user_messages_log = []
