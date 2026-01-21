# English Tutor - Direct Groq Integration
import json
import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

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
        api_key = os.getenv('GROQ_API_KEY', '')
        self.client = Groq(api_key=api_key)
        self.model = os.getenv('MODEL_NAME', 'llama-3.3-70b-versatile')
        self.conversation_history = []
        self.user_messages_log = []  # Store user messages for chat mode feedback
        self.max_history = 20
        self.mode = 'tutor'  # 'tutor' or 'chat'

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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a grammar checker. Respond ONLY with valid JSON, no other text."
                    },
                    {
                        "role": "user",
                        "content": GRAMMAR_CHECK_PROMPT.format(user_message=user_message)
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )

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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=500
            )
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert English language analyst. Provide detailed, constructive feedback. Respond ONLY with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": SESSION_FEEDBACK_PROMPT.format(user_messages=user_messages_text)
                    }
                ],
                temperature=0.5,
                max_tokens=1500
            )

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
