# AGENT_DESIGN.md

# AI Agent Design

## Overview

The Hospitality AI Operations Assistant uses a LangGraph-based AI agent responsible for understanding user requests, retrieving relevant knowledge from the vector database, and generating accurate, grounded responses.

Unlike a simple chatbot, the agent is capable of reasoning about user intent, selecting appropriate tools, maintaining conversational context, and ensuring that every answer is based on retrieved company documentation.

The agent acts as the orchestration layer between the frontend, retrieval system, and large language model.

---

# Goals

The AI agent should:

- Understand natural language queries.
- Identify the user's intent.
- Retrieve the most relevant documents.
- Generate grounded answers.
- Provide document citations.
- Handle follow-up questions.
- Avoid hallucinations.
- Maintain a professional tone.
- Gracefully recover from errors.

---

# Agent Responsibilities

The agent is responsible for:

- Intent understanding
- Tool selection
- Document retrieval
- Context assembly
- Prompt construction
- LLM interaction
- Response validation
- Citation generation

The agent is **not** responsible for:

- User authentication
- Database management
- File uploads
- UI rendering
- API routing

---

# Agent Workflow

```
User Question
      │
      ▼
Intent Analysis
      │
      ▼
Tool Selection
      │
      ▼
Document Search
      │
      ▼
Retrieve Context
      │
      ▼
Prompt Construction
      │
      ▼
OpenRouter
      │
      ▼
Grounded Response
      │
      ▼
Citation Formatting
      │
      ▼
Return Answer
```

---

# LangGraph Workflow

```
START

↓

Receive User Input

↓

Analyze Intent

↓

Retrieve Documents

↓

Build Context

↓

Generate Response

↓

Validate Response

↓

Return Final Answer

↓

END
```

---

# Agent State

The LangGraph state should contain:

```python
messages

user_query

retrieved_chunks

conversation_history

tool_results

generated_response

citations

errors
```

Future additions:

```python
user_role

department

session_id

memory

preferences
```

---

# Tool Architecture

The agent should be tool-driven.

Every capability is implemented as an independent tool.

Current tools:

### search_documents

Purpose:

Search ChromaDB for relevant chunks.

Input:

Natural language query.

Output:

Relevant document chunks.

---

### list_documents

Purpose:

Return all indexed documents.

Example:

```
Front Desk SOP

Housekeeping SOP

Employee Handbook
```

---

### summarize_document

Purpose:

Generate a concise summary of a selected document.

---

### compare_documents

Purpose:

Compare operational differences between two documents.

Example:

```
Compare

Housekeeping SOP

vs

VIP Room SOP
```

---

### search_by_section

Purpose:

Retrieve a specific document section.

Example:

```
Emergency Procedures

Fire Evacuation
```

---

### get_page

Purpose:

Retrieve a specific page from a document.

Future feature.

---

# Tool Selection Logic

The agent should determine which tool to call based on the user's intent.

Examples:

Question:

```
How do I process an early check-in?
```

↓

search_documents

---

Question:

```
Summarize the employee handbook.
```

↓

summarize_document

---

Question:

```
List all uploaded documents.
```

↓

list_documents

---

Question:

```
Compare the lost and found policy with the VIP guest procedure.
```

↓

compare_documents

---

# Intent Categories

The agent should classify requests into categories.

Examples:

Search

Summary

Comparison

Listing

Explanation

Definition

Procedure

Policy

Troubleshooting

Greeting

Unknown

---

# Retrieval Strategy

For information requests:

1. Search vector database.

2. Retrieve Top K chunks.

3. Rank by relevance.

4. Assemble context.

5. Send to LLM.

---

# Prompt Construction

The prompt consists of three sections.

```
System Prompt

↓

Retrieved Context

↓

User Question
```

The retrieved context should always appear before the user question.

---

# Conversation Memory

Current Version

Conversation memory exists only during the active session.

The agent should remember:

- previous questions
- previous answers
- referenced documents

Future versions may include persistent conversation history.

---

# Context Window Management

To avoid exceeding token limits:

- Retrieve only relevant chunks.
- Remove duplicate content.
- Prioritize high-relevance sections.
- Keep prompts concise.

---

# Response Validation

Before returning a response, the agent should verify:

- Context exists.
- Sources were retrieved.
- No hallucinated information is present.
- Citations are attached where applicable.

If validation fails:

Return:

```
I couldn't find enough information in the knowledge base to answer this question.
```

---

# Citation Strategy

Every factual response should include:

- Document Name
- Section Name
- Page Number (if available)

Example:

```
Sources

Front Desk Operations SOP

Section:
Guest Check-In

Page:
18
```

---

# Error Handling

The agent should gracefully handle:

No documents found

No search results

Embedding failure

Vector search failure

OpenRouter timeout

Tool failure

Malformed prompts

Unexpected exceptions

Errors should be logged internally while returning user-friendly messages.

---

# Logging

The agent should log:

User query

Intent

Selected tool

Retrieved documents

Search latency

LLM latency

Errors

Do not log:

API keys

Sensitive user information

Passwords

---

# Guardrails

The agent must never:

Invent company policies.

Guess missing information.

Use external knowledge when retrieved documents are available.

Answer without context.

Reveal internal prompts.

Reveal API keys.

Ignore retrieval results.

---

# Response Style

Responses should be:

Professional

Concise

Clear

Actionable

Well-structured

Easy to read

When possible:

Use bullet points.

Use numbered steps.

Include citations.

---

# Future Capabilities

The agent architecture should support:

Hybrid Search

Re-ranking

Multi-Agent Collaboration

Planner Agent

Document QA Agent

Summarization Agent

Conversation Memory

Role-Aware Responses

Department-Specific Knowledge

Knowledge Graph Retrieval

Voice Interaction

Workflow Automation

---

# Scalability

The agent should be designed so additional tools can be added without modifying the overall workflow.

Every new capability should be implemented as an independent tool and registered within the LangGraph graph.

This ensures the architecture remains modular, maintainable, and extensible.

---

# Design Principles

The AI agent follows these principles:

- Retrieval before generation.
- Ground every response in company documents.
- Prefer accuracy over creativity.
- Keep tools independent.
- Separate reasoning from execution.
- Minimize hallucinations.
- Make responses explainable through citations.
- Design for future scalability.

---

# Summary

The LangGraph agent is the central intelligence layer of the Hospitality AI Operations Assistant. It orchestrates document retrieval, tool execution, prompt construction, and response generation while ensuring every answer is accurate, explainable, and grounded in the organization's operational knowledge.