from typing import List, Dict, Any, TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    retrieved_chunks: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    errors: List[str]
    intent_result: Dict[str, Any]
