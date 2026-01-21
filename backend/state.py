# State definition
from typing import TypedDict, List, Dict, Any, Optional


class TutorState(TypedDict, total=False):
    """State for the English Tutor AI workflow"""

    # User input
    user_message: str
    user_id: Optional[str]
    session_id: Optional[str]

    # Analysis results
    analysis: Dict[str, Any]

    # Grammar checking
    grammar_errors: List[Dict[str, str]]
    corrections: List[Dict[str, str]]

    # AI response
    ai_response: str

    # Feedback
    feedback: Dict[str, Any]

    # Conversation history
    conversation_history: List[Dict[str, str]]

    # User profile
    user_level: str  # beginner, intermediate, advanced
    learning_goals: List[str]
