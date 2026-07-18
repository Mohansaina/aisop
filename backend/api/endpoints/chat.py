import json
import uuid
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from backend.core.database import get_db_connection
from backend.agent.graph import agent_graph

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    answer: str
    conversation_id: str
    citations: list

@router.post("/chat", response_model=ChatResponse)
def post_chat(request: ChatRequest):
    """
    Submit a message to the AI operations agent. Handles session updates and history logging.
    """
    message_text = request.message.strip()
    if not message_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    conv_id = request.conversation_id
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Initialize conversation if new
    if not conv_id:
        conv_id = str(uuid.uuid4())
        # Generate title from the first query (first 40 characters)
        title = message_text[:40] + "..." if len(message_text) > 40 else message_text
        cursor.execute(
            "INSERT INTO conversations (id, title) VALUES (?, ?)",
            (conv_id, title)
        )
        conn.commit()
    else:
        # Check if conversation exists
        cursor.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Conversation session not found.")

    # 2. Insert User Message
    user_msg_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, 'user', ?)",
        (user_msg_id, conv_id, message_text)
    )
    conn.commit()

    # 3. Retrieve conversation history to feed into the agent (optional context)
    cursor.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,)
    )
    history_rows = cursor.fetchall()
    
    # 4. Invoke LangGraph agent graph
    state_input = {
        "user_query": message_text,
        "messages": [{"role": row["role"], "content": row["content"]} for row in history_rows],
        "retrieved_chunks": [],
        "citations": [],
        "errors": []
    }
    
    try:
        final_state = agent_graph.invoke(state_input)
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")

    # Extract answer and citations
    assistant_content = ""
    # Get last message from state
    if final_state.get("messages"):
        last_msg = final_state["messages"][-1]
        # Depending on message representation, it could be a dict or a Message object
        if hasattr(last_msg, "content"):
            assistant_content = last_msg.content
        elif isinstance(last_msg, dict):
            assistant_content = last_msg.get("content", "")
        else:
            assistant_content = str(last_msg)

    citations = final_state.get("citations", [])

    # 5. Save Assistant Response
    assistant_msg_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO messages (id, conversation_id, role, content, citations) VALUES (?, ?, 'assistant', ?, ?)",
        (assistant_msg_id, conv_id, assistant_content, json.dumps(citations))
    )
    
    # Update conversation timestamp
    cursor.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (conv_id,))
    conn.commit()
    conn.close()

    return ChatResponse(
        success=True,
        answer=assistant_content,
        conversation_id=conv_id,
        citations=citations
    )

@router.get("/conversations")
def get_conversations():
    """
    List all chat sessions.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.get("/conversations/{id}")
def get_conversation(id: str):
    """
    Retrieve all message records for a specific conversation session.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?", (id,))
    conv = cursor.fetchone()
    if not conv:
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found.")
        
    cursor.execute("SELECT id, role, content, citations, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (id,))
    msg_rows = cursor.fetchall()
    conn.close()

    messages = []
    for r in msg_rows:
        citations_list = []
        if r["citations"]:
            try:
                citations_list = json.loads(r["citations"])
            except Exception:
                pass
        messages.append({
            "id": r["id"],
            "role": r["role"],
            "content": r["content"],
            "citations": citations_list,
            "created_at": r["created_at"]
        })

    return {
        "success": True,
        "data": {
            "conversation": dict(conv),
            "messages": messages
        }
    }

@router.delete("/conversations/{id}")
def delete_conversation(id: str):
    """
    Delete a conversation session.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM conversations WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found.")
        
    cursor.execute("DELETE FROM conversations WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Conversation deleted successfully."}
