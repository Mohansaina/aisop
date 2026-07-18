# ARCHITECTURE.md

# System Architecture

## Overview

Hospitality AI Operations Assistant is a Retrieval-Augmented Generation (RAG) application designed to provide hotel employees with accurate answers from internal operational documentation.

The system follows a modular architecture with clear separation between the frontend, backend, AI agent, vector database, and storage layers.

The architecture prioritizes scalability, maintainability, and production readiness.

---

# High-Level Architecture

```
                    User
                      │
                      ▼
        ┌────────────────────────┐
        │      Next.js UI         │
        │ React + Tailwind +      │
        │ shadcn/ui               │
        └────────────┬────────────┘
                     │ REST API
                     ▼
        ┌────────────────────────┐
        │      FastAPI           │
        │ API Layer              │
        └────────────┬────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │    LangGraph Agent      │
        └────────────┬────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
 Search Documents         Other Tools
         │
         ▼
   Chroma Vector DB
         │
         ▼
 Retrieved Chunks
         │
         ▼
   OpenRouter LLM
         │
         ▼
 Generated Answer
         │
         ▼
      Frontend
```

---

# Core Components

The application consists of five primary layers.

## Presentation Layer

Responsible for user interaction.

Technology:

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui

Responsibilities:

- Chat interface
- Admin dashboard
- Document management
- Upload interface
- Display citations
- Conversation history
- Loading and error states

---

## API Layer

Technology:

FastAPI

Responsibilities:

- Expose REST APIs
- Validate requests
- Authenticate users (future)
- Route requests
- Handle uploads
- Communicate with LangGraph
- Return structured responses

No business logic should exist in API routes.

---

## AI Layer

Technology:

LangGraph

Responsibilities:

- Understand user intent
- Decide which tools to call
- Retrieve context
- Build prompts
- Call OpenRouter
- Return grounded responses

The AI layer should remain independent from the API layer.

---

## Retrieval Layer

Technology:

ChromaDB

Responsibilities:

- Store embeddings
- Search similar chunks
- Return ranked results
- Filter metadata
- Support future hybrid search

---

## Storage Layer

SQLite stores structured application data.

Examples:

- uploaded documents
- chat history
- users
- conversations
- metadata
- indexing status

---

# Request Lifecycle

## Chat Request

1. User submits a question.

2. Frontend sends request to FastAPI.

3. FastAPI validates the request.

4. LangGraph receives the query.

5. Search tool retrieves relevant chunks.

6. ChromaDB performs similarity search.

7. Retrieved context is assembled.

8. OpenRouter generates the response.

9. Citations are attached.

10. Response is returned to frontend.

---

# Document Upload Lifecycle

1. Upload PDF.

2. Validate document.

3. Extract text.

4. Clean text.

5. Chunk document.

6. Generate embeddings.

7. Store vectors.

8. Store metadata.

9. Mark indexing complete.

---

# Project Structure

```
hospitality-ai/

frontend/
backend/
agent/
database/
knowledge/
docs/
scripts/
```

---

# Frontend Architecture

```
app/

components/

hooks/

lib/

services/

types/

styles/
```

Responsibilities:

app/
Application routes

components/
Reusable UI

services/
API calls

hooks/
React hooks

types/
TypeScript models

---

# Backend Architecture

```
backend/

api/

services/

repositories/

models/

schemas/

utils/

core/
```

Responsibilities:

api/
REST endpoints

services/
Business logic

repositories/
Database access

models/
Database models

schemas/
Pydantic validation

utils/
Shared helpers

core/
Configuration

---

# Agent Architecture

```
agent/

graph.py

tools/

prompts/

state.py

memory.py
```

Responsibilities

graph.py

Main LangGraph workflow

tools/

Search tools

prompts/

Prompt templates

state.py

Conversation state

memory.py

Future memory implementation

---

# Data Flow

```
Question

↓

Intent Detection

↓

Document Search

↓

Similarity Ranking

↓

Context Assembly

↓

Prompt Construction

↓

LLM

↓

Grounded Answer

↓

Citation Generation

↓

User
```

---

# Retrieval Architecture

The retrieval pipeline consists of:

Document

↓

Text Extraction

↓

Cleaning

↓

Chunking

↓

Embedding Generation

↓

Vector Storage

↓

Similarity Search

↓

Retrieved Context

---

# Database Architecture

SQLite stores structured data.

Tables include:

Documents

Chunks

Users

Messages

Conversations

Uploads

Indexes should be added for:

Document IDs

Conversation IDs

Chunk IDs

---

# Vector Database Architecture

ChromaDB stores:

Embedding vectors

Metadata

Document identifiers

Section names

Page numbers

Department names

Embedding model:

sentence-transformers/all-MiniLM-L6-v2

---

# External Services

OpenRouter

Purpose:

LLM inference

Future services may include:

Cloud Storage

Authentication Provider

Monitoring

Analytics

---

# Error Handling

Every layer should handle errors independently.

Frontend

Display friendly messages.

Backend

Return structured JSON.

Agent

Recover gracefully from tool failures.

Database

Rollback failed transactions.

---

# Logging Strategy

Log:

API requests

Document uploads

Indexing

Search latency

Tool execution

LLM latency

Errors

Do not log:

API keys

Passwords

Sensitive information

---

# Security Architecture

Future authentication:

JWT

Role-based access

Admin permissions

User permissions

All uploads must be validated before processing.

Secrets must only exist on the backend.

---

# Scalability

The architecture should allow future migration to:

PostgreSQL

Redis

Qdrant

Pinecone

Azure AI Search

AWS

Docker

Kubernetes

without major code changes.

---

# Design Principles

The architecture follows these principles:

- Separation of Concerns
- Single Responsibility Principle
- Modular Design
- Reusable Components
- Strong Typing
- Stateless APIs
- Extensible Agent Design
- Maintainability
- Testability
- Production Readiness

---

# Future Architecture

Planned additions include:

- Authentication
- Multi-user support
- Role-based access control
- Conversation memory
- Hybrid search
- Re-ranking
- Multi-agent workflows
- Cloud deployment
- Monitoring
- Analytics dashboard
- Voice assistant
- Mobile application

---

# Conclusion

The Hospitality AI Operations Assistant is designed as a modular, enterprise-grade RAG system. Each layer has a clearly defined responsibility, enabling independent development, testing, and future scaling while maintaining clean architecture principles and a reliable user experience.