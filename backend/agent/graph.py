import json
import httpx
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from backend.core.config import settings
from backend.agent.state import AgentState
from backend.agent.prompts import SYSTEM_PROMPT, INTENT_PROMPT
from backend.agent.tools import search_documents, list_documents, retrieve_all_document_chunks, get_document_by_title

def call_llm(messages: List[Dict[str, str]]) -> str:
    """
    Sends messages to OpenRouter API. Fallback messages are generated if keys are missing.
    """
    if not settings.OPENROUTER_API_KEY:
        return "System Status: Configuration is incomplete. Please set the `OPENROUTER_API_KEY` environment variable in the backend to enable natural language generation."

    # Serialize message history elements to plain dicts to avoid JSON serialization crash
    formatted_messages = []
    for msg in messages:
        if isinstance(msg, dict):
            formatted_messages.append(msg)
        else:
            role = "user"
            if hasattr(msg, "type"):
                if msg.type == "human" or msg.type == "user":
                    role = "user"
                elif msg.type == "ai" or msg.type == "assistant":
                    role = "assistant"
                elif msg.type == "system":
                    role = "system"
            formatted_messages.append({"role": role, "content": getattr(msg, "content", str(msg))})

    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    if settings.OPENROUTER_API_KEY.startswith("nvapi-"):
        # Nvidia Integrate API Multi-Tier Fallback
        api_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
        # Tier 1: Try flagship Llama 3.3 70B with a snappy 15-second timeout
        payload = {
            "model": "meta/llama-3.3-70b-instruct",
            "messages": formatted_messages,
            "temperature": 0.1
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(api_url, headers=headers, json=payload)
                res.raise_for_status()
                return res.json()["choices"][0]["message"]["content"]
        except Exception:
            # Tier 2: Fallback to Llama 3.1 8B (ultra-low latency, under 100ms)
            payload["model"] = "meta/llama-3.1-8b-instruct"
            try:
                with httpx.Client(timeout=25.0) as client:
                    res = client.post(api_url, headers=headers, json=payload)
                    res.raise_for_status()
                    return res.json()["choices"][0]["message"]["content"]
            except Exception as e:
                return f"I encountered an error trying to connect to the AI service: {str(e)}."
    else:
        # Standard OpenRouter flow
        headers["HTTP-Referer"] = "http://localhost:3000"
        headers["X-Title"] = "Hospitality AI Operations Assistant"
        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": formatted_messages,
            "temperature": 0.1
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(api_url, headers=headers, json=payload)
                res.raise_for_status()
                return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"I encountered an error trying to connect to the AI service: {str(e)}."

def analyze_intent_node(state: AgentState) -> Dict[str, Any]:
    """
    Classifies the user query's intent (GREETING, LIST_DOCUMENTS, SUMMARIZE_DOCUMENT, COMPARE_DOCUMENTS, or SEARCH)
    entirely locally without making OpenRouter LLM calls to preserve rate limits.
    """
    query = state["user_query"]
    query_lower = query.lower().strip()
    
    # 1. Greetings
    greetings = ["hi", "hello", "hey", "who are you", "help", "good morning", "good afternoon", "good evening", "greetings"]
    if any(x == query_lower or query_lower.startswith(x + " ") for x in greetings):
        return {"intent_result": {"intent": "GREETING"}}
        
    # 2. List documents
    list_keywords = ["list documents", "show files", "what sop", "list policies", "what manuals", "show documents", "available files", "indexed documents"]
    if any(x in query_lower for x in list_keywords):
        return {"intent_result": {"intent": "LIST_DOCUMENTS"}}
        
    # 3. Compare documents
    compare_keywords = ["compare", "comparison", "contrast", "difference between", "differences between"]
    if any(x in query_lower for x in compare_keywords):
        docs = list_documents()
        matched_docs = []
        for d in docs:
            title_clean = d["title"].lower().replace("_", " ").replace("-", " ")
            if title_clean in query_lower or d["filename"].lower() in query_lower:
                matched_docs.append(d["title"])
        if len(matched_docs) >= 2:
            return {"intent_result": {
                "intent": "COMPARE_DOCUMENTS",
                "target_document_1": matched_docs[0],
                "target_document_2": matched_docs[1]
            }}
            
    # 4. Summarize document
    summarize_keywords = ["summarize", "summary of", "overview of", "synopsis of"]
    if any(x in query_lower for x in summarize_keywords):
        docs = list_documents()
        for d in docs:
            title_clean = d["title"].lower().replace("_", " ").replace("-", " ")
            if title_clean in query_lower or d["filename"].lower() in query_lower:
                return {"intent_result": {
                    "intent": "SUMMARIZE_DOCUMENT",
                    "target_document_1": d["title"]
                }}

    # 5. Default Fallback to general Search / RAG
    return {"intent_result": {"intent": "SEARCH"}}

def execute_intent_node(state: AgentState) -> Dict[str, Any]:
    """
    Retrieves information based on classified intent and builds context.
    """
    intent_data = state.get("intent_result", {"intent": "SEARCH"})
    intent = intent_data.get("intent", "SEARCH")
    query = state["user_query"]
    
    retrieved_chunks = []
    citations = []
    
    if intent == "GREETING":
        answer = ("Hello! I am your Hospitality AI Operations Assistant. "
                  "I can help you search, summarize, or compare your hotel's standard operating procedures (SOPs), "
                  "manuals, and policies. How can I assist you today?")
        return {"messages": [{"role": "assistant", "content": answer}]}
        
    elif intent == "LIST_DOCUMENTS":
        docs = list_documents()
        if not docs:
            answer = "There are no documents indexed in the knowledge base at this moment."
        else:
            doc_list = "\n".join([f"- **{d['title']}** (Dept: {d['department']}, Status: {d['status']})" for d in docs])
            answer = f"Here are the currently indexed documents in the knowledge base:\n\n{doc_list}"
        return {"messages": [{"role": "assistant", "content": answer}]}
        
    elif intent == "SUMMARIZE_DOCUMENT":
        target = intent_data.get("target_document_1", "")
        doc_meta = get_document_by_title(target) if target else None
        if not doc_meta:
            # Try to list matching titles
            docs = list_documents()
            if docs:
                doc_list = ", ".join([f"'{d['title']}'" for d in docs])
                answer = f"I couldn't identify the document you want summarized. Currently available documents are: {doc_list}."
            else:
                answer = "I couldn't find any documents to summarize."
            return {"messages": [{"role": "assistant", "content": answer}]}
            
        chunks = retrieve_all_document_chunks(doc_meta["id"])
        if not chunks:
            return {"messages": [{"role": "assistant", "content": f"No content chunks found for document '{doc_meta['title']}'."}]}
            
        # Join chunks up to model capacity (say, top 8 chunks to avoid blowing token count)
        summary_context = "\n\n".join([c["text"] for c in chunks[:8]])
        prompt = f"Summarize the following document. Highlight its Purpose, key SOP steps, and essential checklists:\n\n{summary_context}"
        messages = [
            {"role": "system", "content": "You are a professional hospitality analyst. Provide clear, bulleted summaries."},
            {"role": "user", "content": prompt}
        ]
        summary = call_llm(messages)
        return {
            "messages": [{"role": "assistant", "content": summary}],
            "citations": [{"filename": doc_meta["filename"], "section": "Full Summary", "page": "All"}]
        }

    elif intent == "COMPARE_DOCUMENTS":
        target1 = intent_data.get("target_document_1", "")
        target2 = intent_data.get("target_document_2", "")
        doc_meta1 = get_document_by_title(target1) if target1 else None
        doc_meta2 = get_document_by_title(target2) if target2 else None
        
        if not doc_meta1 or not doc_meta2:
            return {"messages": [{"role": "assistant", "content": "I need two specific documents to perform a comparison. Please clarify which documents you want to compare."}]}
            
        chunks1 = retrieve_all_document_chunks(doc_meta1["id"])
        chunks2 = retrieve_all_document_chunks(doc_meta2["id"])
        
        context1 = "\n\n".join([c["text"] for c in chunks1[:5]])
        context2 = "\n\n".join([c["text"] for c in chunks2[:5]])
        
        prompt = (f"Compare the operations, checklists, and key standards between these two documents.\n\n"
                  f"Document 1: {doc_meta1['title']}\nContent:\n{context1}\n\n"
                  f"Document 2: {doc_meta2['title']}\nContent:\n{context2}\n\n"
                  f"Provide a structured comparison highlighting differences and similarities.")
                  
        messages = [
            {"role": "system", "content": "You are an operations manager. Compare these procedures clearly."},
            {"role": "user", "content": prompt}
        ]
        comparison = call_llm(messages)
        return {
            "messages": [{"role": "assistant", "content": comparison}],
            "citations": [
                {"filename": doc_meta1["filename"], "section": "Comparison", "page": "N/A"},
                {"filename": doc_meta2["filename"], "section": "Comparison", "page": "N/A"}
            ]
        }
        
    else: # SEARCH / RAG Intent
        search_query = query
        # Local query aggregation heuristic to resolve pronouns without an extra API call
        if len(state["messages"]) > 1:
            prev_user_queries = []
            for msg in state["messages"][:-1]:
                role = getattr(msg, "role", getattr(msg, "type", ""))
                content = getattr(msg, "content", "")
                if role in ("user", "human") and content:
                    prev_user_queries.append(content)
            
            # If the current query is a follow-up (e.g., contains pronouns or is short), merge keywords
            pronouns = ["it", "he", "she", "they", "them", "these", "those", "rules", "procedures", "steps", "standards", "details"]
            query_lower = query.lower()
            needs_context = len(query.split()) < 4 or any(p in query_lower for p in pronouns)
            
            if needs_context and prev_user_queries:
                # Merge key terms from previous user query to retain topical focus
                last_query = prev_user_queries[-1]
                # Filter out standard question words to create clean search terms
                stop_words = {"what", "is", "are", "the", "for", "how", "to", "do", "we", "i", "can", "you", "tell", "me", "about"}
                keywords = [word for word in last_query.lower().split() if word not in stop_words]
                if keywords:
                    search_query = f"{' '.join(keywords)} {query}"

        results = search_documents(search_query, limit=7)
        context_blocks = []
        if results:
            for res in results:
                meta = res.get("metadata", {})
                if meta:
                    block = (f"Document: {meta.get('filename', '')}\n"
                             f"Section: {meta.get('section', 'General')}\n"
                             f"Page: {meta.get('page_number', 1)}\n"
                             f"Content:\n{res['text']}")
                    context_blocks.append(block)
                    
                    citations.append({
                        "filename": meta.get("filename", ""),
                        "section": meta.get("section", "General"),
                        "page": meta.get("page_number", 1)
                    })
            
        context_str = "\n\n---\n\n".join(context_blocks)
        
        system_content = f"{SYSTEM_PROMPT}\n\nRetrieved Context:\n{context_str}"
        messages = [{"role": "system", "content": system_content}]
        # Append last 6 messages from conversation log for context
        messages.extend(state["messages"][-6:])
        
        answer = call_llm(messages)
        # Fallback to local RAG extraction if the cloud LLM provider is blocked/rate-limited
        if "error" in answer.lower() or "429" in answer or "402" in answer or "payment" in answer.lower():
            if results:
                fallback_intro = (
                    "⚠️ **Local Retrieval Mode** (Cloud AI Service Rate-Limited)\n\n"
                    "I retrieved the following operational sections directly from your Standard Operating Procedures:\n\n"
                )
                paragraphs = []
                for i, res in enumerate(results[:3], 1):
                    meta = res.get("metadata", {})
                    clean_text = res["text"].strip()
                    if len(clean_text) > 450:
                        clean_text = clean_text[:450] + "..."
                    paragraphs.append(
                        f"### {i}. {meta.get('filename', '').replace('.md', '')} — *{meta.get('section', 'General')}*\n"
                        f"{clean_text}\n"
                    )
                answer = fallback_intro + "\n".join(paragraphs)
            else:
                answer = "⚠️ **Connection Error**: The cloud AI service is currently rate-limited, and no local operational documents match your general question. Please try again or check your API key credits."

        return {
            "messages": [{"role": "assistant", "content": answer}],
            "citations": citations,
            "retrieved_chunks": results
        }

# Build LangGraph workflow
workflow = StateGraph(AgentState)

workflow.add_node("analyze_intent", analyze_intent_node)
workflow.add_node("execute_intent", execute_intent_node)

workflow.set_entry_point("analyze_intent")
workflow.add_edge("analyze_intent", "execute_intent")
workflow.add_edge("execute_intent", END)

agent_graph = workflow.compile()
