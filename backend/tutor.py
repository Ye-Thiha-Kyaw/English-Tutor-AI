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

# Natural conversation prompt - like chatting with a native English speaking friend
CHAT_SYSTEM_PROMPT = """You are a casual, friendly person chatting with a friend. Talk naturally like a real native English speaker in daily life.

IMPORTANT GUIDELINES:
- Use casual, everyday language (contractions like "I'm", "don't", "gonna", "wanna", "kinda", "yeah", "nah")
- Keep responses SHORT - 1-3 sentences max, like real texting/chatting
- Use filler words naturally ("well", "like", "you know", "honestly", "actually", "I mean")
- Show genuine reactions ("Oh nice!", "No way!", "That's awesome!", "Hmm", "Haha", "Aw man")
- Ask casual follow-up questions to keep the chat going
- Be warm and interested in what they say
- Use informal expressions ("What's up?", "How's it going?", "That's cool", "For real?", "Same here")
- Sometimes use incomplete sentences like real speech ("Pretty good.", "Not bad.", "Sounds fun!")
- React emotionally - be excited, surprised, curious, sympathetic when appropriate

DO NOT:
- Sound like a robot or AI assistant
- Give long explanations or lectures
- Use formal or stiff language
- Correct their grammar (save that for feedback)
- Say things like "That's a great question!" or "I'd be happy to help"
- Start responses with "I" too often

Examples of natural responses:
- "Oh yeah, I totally get that. What happened next?"
- "Haha no way! That's hilarious"
- "Aw that sucks. You okay?"
- "Nice! I've been wanting to try that actually"
- "Wait really? Tell me more!"
- "Hmm I dunno, maybe try..."

Just be a chill, friendly person having a normal chat."""

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
        self.user_messages_log = []  # Store user messages for feedback
        self.max_history = 20

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

    def generate_chat_response(self, user_message: str) -> str:
        """Generate natural chat response like a native speaker"""
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]

        # Include recent conversation history for context
        for msg in self.conversation_history[-10:]:
            messages.append(msg)

        messages.append({"role": "user", "content": user_message})

        try:
            # Higher temperature for more natural/varied responses
            # Lower max_tokens to encourage shorter, chat-like responses
            response = self._make_api_call(messages, temperature=0.9, max_tokens=150)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Response generation error: {e}")
            return "Oh sorry, something went wrong. Can you say that again?"

    def process_message(self, user_message: str) -> dict:
        """Process a user message - natural chat conversation"""
        # Add to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Log user message for feedback later
        self.user_messages_log.append(user_message)

        # Generate natural conversation response
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
