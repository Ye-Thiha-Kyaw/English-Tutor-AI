# Graph nodes (functions)
import json
from groq import Groq
from state import TutorState
from config import config
from prompts import SYSTEM_PROMPT, GRAMMAR_CHECK_PROMPT, RESPONSE_PROMPT

# Initialize Groq client
client = Groq(api_key=config.GROQ_API_KEY)


def analyze_input(state: TutorState) -> TutorState:
    """Analyze the user's input for context and intent"""
    user_message = state.get('user_message', '')

    state['analysis'] = {
        'intent': 'conversation',
        'topic': 'general',
        'complexity': 'intermediate'
    }

    return state


def check_grammar(state: TutorState) -> TutorState:
    """Check grammar and identify errors using Groq"""
    user_message = state.get('user_message', '')

    try:
        response = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a grammar checker. Analyze text for grammar errors and respond ONLY with valid JSON."
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

        # Try to parse JSON from response
        try:
            # Find JSON in response
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = result_text[start_idx:end_idx]
                result = json.loads(json_str)
                state['grammar_errors'] = result.get('errors', [])
                state['corrections'] = result.get('errors', [])
            else:
                state['grammar_errors'] = []
                state['corrections'] = []
        except json.JSONDecodeError:
            state['grammar_errors'] = []
            state['corrections'] = []

    except Exception as e:
        print(f"Grammar check error: {e}")
        state['grammar_errors'] = []
        state['corrections'] = []

    return state


def generate_response(state: TutorState) -> TutorState:
    """Generate AI tutor response using Groq"""
    user_message = state.get('user_message', '')
    corrections = state.get('corrections', [])
    user_level = state.get('user_level', 'intermediate')
    conversation_history = state.get('conversation_history', [])

    # Build messages with conversation history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history (last 10 messages)
    for msg in conversation_history[-10:]:
        messages.append(msg)

    # Add current user message with context
    prompt = RESPONSE_PROMPT.format(
        user_message=user_message,
        corrections=json.dumps(corrections) if corrections else "None",
        user_level=user_level
    )
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=messages,
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS
        )

        state['ai_response'] = response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Response generation error: {e}")
        state['ai_response'] = "I'm sorry, I encountered an error. Please try again."

    return state


def provide_feedback(state: TutorState) -> TutorState:
    """Provide educational feedback to the user"""
    corrections = state.get('corrections', [])

    tips = []
    if corrections:
        for error in corrections[:3]:  # Limit to 3 tips
            if 'explanation' in error:
                tips.append(error['explanation'])

    state['feedback'] = {
        'encouragement': 'Keep practicing!' if not corrections else 'Good effort! Let\'s work on these points.',
        'tips': tips,
        'next_steps': []
    }

    return state
