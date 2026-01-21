# LangGraph workflow
from langgraph.graph import StateGraph, END
from state import TutorState
from nodes import (
    analyze_input,
    check_grammar,
    generate_response,
    provide_feedback
)


def create_tutor_graph():
    """Create the LangGraph workflow for the English tutor"""

    workflow = StateGraph(TutorState)

    # Add nodes
    workflow.add_node("analyze_input", analyze_input)
    workflow.add_node("check_grammar", check_grammar)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("provide_feedback", provide_feedback)

    # Define edges
    workflow.set_entry_point("analyze_input")
    workflow.add_edge("analyze_input", "check_grammar")
    workflow.add_edge("check_grammar", "generate_response")
    workflow.add_edge("generate_response", "provide_feedback")
    workflow.add_edge("provide_feedback", END)

    return workflow.compile()


# Create the graph instance
tutor_graph = create_tutor_graph()
