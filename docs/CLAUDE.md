# CLAUDE.md

# Hospitality AI Operations Assistant

## Project Overview

This project is an AI-powered Operations Assistant for the hospitality industry.

The application enables hotel employees to ask natural language questions and receive accurate, grounded answers from internal company documents such as Standard Operating Procedures (SOPs), employee manuals, policies, training guides, and operational documentation.

This project is intended to simulate an enterprise-grade internal knowledge management system similar to those used by Marriott, Hilton, Hyatt, Four Seasons, and other international hospitality brands.

The primary goal is to demonstrate modern AI engineering practices using Retrieval-Augmented Generation (RAG), AI agents, vector databases, and modern web technologies.

---

# Project Vision

Build a modern AI Operations Assistant that becomes the single source of truth for hospitality operations.

Employees should never need to manually search through hundreds of pages of SOPs.

Instead they simply ask questions like:

> How do I process an early check-in?

> What is the lost and found procedure?

> How should a VIP guest be handled?

> What are the food safety temperature requirements?

The AI searches the company's knowledge base and returns an accurate answer with citations.

---

# Project Goals

The assistant must:

- Answer operational questions accurately
- Never hallucinate policies
- Always use retrieved document context
- Cite source documents
- Respond within a few seconds
- Feel like an enterprise internal tool
- Be scalable for future features

---

# Tech Stack

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui

## Backend

- FastAPI
- Python

## AI

- LangGraph
- OpenRouter
- sentence-transformers
- all-MiniLM-L6-v2

## Vector Database

- ChromaDB

## Database

- SQLite

---

# Architecture

User

↓

Next.js Frontend

↓

FastAPI API

↓

LangGraph Agent

↓

Search Tool

↓

ChromaDB

↓

Relevant Chunks

↓

OpenRouter

↓

Grounded Response

↓

Frontend

---

# Knowledge Base

The AI operates exclusively on uploaded internal documentation.

Example document categories:

- Front Desk Operations
- Guest Check-In
- Guest Check-Out
- Housekeeping
- Maintenance
- Food Safety
- Reservation Management
- Employee Handbook
- Customer Service
- Emergency Procedures
- VIP Guest Handling
- Lost & Found

Documents are indexed into ChromaDB using embeddings.

The AI must answer only from indexed documents.

---

# AI Behavior

The AI is an internal hospitality operations assistant.

It should:

- be professional
- be concise
- be factual
- never guess
- never invent procedures
- always use retrieved context
- provide citations whenever possible

If information is unavailable:

"I couldn't find this information in the current knowledge base."

Never fabricate answers.

---

# LangGraph Agent Responsibilities

The agent should:

- understand user intent
- search relevant documents
- retrieve the best chunks
- build context
- generate grounded responses
- cite document sources

Future capabilities may include:

- summarizing documents
- comparing policies
- listing documents
- retrieving document sections
- answering follow-up questions

---

# Coding Philosophy

Write code that is:

- clean
- modular
- reusable
- readable
- maintainable
- production-ready

Avoid unnecessary complexity.

Prefer simple solutions.

Never duplicate logic.

---

# Project Structure

frontend/
    Next.js application

backend/
    FastAPI application

agent/
    LangGraph workflows

knowledge/
    Uploaded documents

database/
    SQLite

docs/
    Project documentation

scripts/
    Utility scripts

---

# Code Standards

Always:

- use TypeScript on frontend
- use Python typing
- write descriptive variable names
- write docstrings
- use dependency injection where appropriate
- separate business logic from API routes

Avoid:

- magic numbers
- deeply nested code
- duplicated logic
- hardcoded values

---

# Frontend Standards

Use:

- shadcn/ui components
- Tailwind CSS
- Responsive layouts
- Dark mode compatibility

Pages should:

- load quickly
- handle errors gracefully
- show loading states
- show empty states

---

# Backend Standards

Use:

- FastAPI routers
- Pydantic models
- Services layer
- Repository pattern where appropriate

Business logic must not live inside API routes.

---

# API Design

Use REST APIs.

Consistent response format.

Example:

Success

{
  "success": true,
  "data": {}
}

Error

{
  "success": false,
  "message": "Document not found"
}

---

# RAG Pipeline

Document Upload

↓

Text Extraction

↓

Cleaning

↓

Chunking

↓

Embeddings

↓

Store in ChromaDB

↓

Similarity Search

↓

Prompt Construction

↓

OpenRouter

↓

Answer Generation

↓

Citation Generation

---

# Chunking Strategy

Use semantic chunking.

Recommended:

Chunk Size:
700–1000 characters

Overlap:
150–200 characters

Store metadata including:

- filename
- page
- section
- heading
- document id

---

# Vector Search

Use similarity search.

Retrieve Top K chunks.

Default:

Top K = 5

Support metadata filtering in the future.

---

# Error Handling

Never crash.

Always return meaningful errors.

Log exceptions.

Handle:

- missing documents
- invalid uploads
- API failures
- vector search failures
- LLM failures

Gracefully.

---

# Logging

Log:

- uploads
- searches
- agent execution
- tool calls
- API errors
- indexing duration

Avoid logging sensitive information.

---

# Security

Validate uploads.

Supported files:

- PDF
- Markdown

Reject unsupported formats.

Protect API keys.

Never expose secrets to frontend.

Sanitize user input.

Prepare for prompt injection attacks.

---

# Performance Goals

Chat response:

<5 seconds

Document upload:

<30 seconds

Search latency:

<500 ms

UI should remain responsive.

---

# User Experience

The application should feel like an enterprise internal tool.

The interface should be:

- minimal
- clean
- professional
- intuitive

Avoid unnecessary animations.

Prioritize usability.

---

# Future Features

Authentication

Role-based permissions

Conversation history

Voice interface

Analytics dashboard

Slack integration

Microsoft Teams integration

Multi-language support

Hybrid search

Re-ranking

Multi-agent workflows

---

# Things Claude Must Never Do

Never hallucinate.

Never invent company policies.

Never answer without retrieved context.

Never hardcode secrets.

Never ignore type safety.

Never place business logic inside UI components.

Never duplicate code unnecessarily.

Never sacrifice readability for cleverness.

---

# Definition of Done

A feature is complete only if:

- Code is clean
- Types are correct
- Error handling exists
- UI is responsive
- Documentation is updated
- Feature has been manually tested
- No obvious bugs remain

---

# Development Workflow

1. Understand the requirement.
2. Design the solution.
3. Implement backend.
4. Implement frontend.
5. Connect AI logic.
6. Test thoroughly.
7. Refactor if necessary.
8. Update documentation.

Always prioritize maintainability over speed.

---

# Final Principle

Build this project as if it will be used by a real hotel with hundreds of employees.

Every design decision should prioritize clarity, reliability, scalability, and maintainability.

When in doubt, choose the solution that is simpler, easier to understand, and easier to extend in the future.