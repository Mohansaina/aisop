# API_SPECIFICATION.md

# API Specification

## Overview

The Hospitality AI Operations Assistant exposes a RESTful API built using FastAPI.

The API serves as the communication layer between the frontend, AI agent, vector database, and storage layer.

All responses follow a consistent JSON format to simplify frontend integration and error handling.

Base URL (Development)

```
http://localhost:8000/api/v1
```

Future Production URL

```
https://api.hospitalityai.com/api/v1
```

---

# API Design Principles

The API should be:

- RESTful
- Stateless
- Versioned
- Consistent
- Well documented
- Secure
- Easy to extend

---

# Response Format

## Success

```json
{
    "success": true,
    "message": "Operation completed successfully.",
    "data": {}
}
```

---

## Error

```json
{
    "success": false,
    "message": "Document not found.",
    "errors": {}
}
```

---

# Authentication

## Current Version

Authentication is disabled for MVP.

---

## Future

JWT Authentication

Bearer Tokens

Refresh Tokens

Role Based Access Control

---

# Endpoints

---

# Health

## GET /health

Purpose

Check whether the API is running.

Response

```json
{
    "status": "healthy",
    "version": "1.0.0"
}
```

Status Codes

200 OK

---

# Upload Document

## POST /documents/upload

Purpose

Upload a new knowledge base document.

Request

Multipart Form Data

```
file

department

document_type
```

Response

```json
{
    "success": true,
    "document_id": "uuid",
    "status": "processing"
}
```

Possible Errors

400 Invalid file

413 File too large

500 Processing failed

---

# List Documents

## GET /documents

Purpose

Return all indexed documents.

Response

```json
[
    {
        "id":"...",
        "title":"Front Desk SOP",
        "department":"Front Office",
        "status":"Indexed"
    }
]
```

---

# Get Document

## GET /documents/{document_id}

Purpose

Retrieve document metadata.

Returns

Title

Department

Pages

Upload Date

Status

---

# Delete Document

## DELETE /documents/{document_id}

Purpose

Delete a document and its vectors.

Response

```json
{
    "success": true
}
```

Deletes

SQLite metadata

Chroma vectors

Upload record

---

# Re-index Document

## POST /documents/{document_id}/reindex

Purpose

Rebuild embeddings.

Response

```json
{
    "status":"processing"
}
```

---

# Chat

## POST /chat

Purpose

Send a question to the AI.

Request

```json
{
    "message":"How do I process an early check-in?",
    "conversation_id":"optional"
}
```

Response

```json
{
    "success": true,
    "answer":"...",
    "citations":[]
}
```

---

# Streaming Chat

## POST /chat/stream

Future Feature

Streams tokens to the frontend.

Suitable for:

Long answers

Typing animation

---

# Conversation History

## GET /conversations

Purpose

Return previous conversations.

Response

```json
[
    {
        "id":"...",
        "title":"Guest Check-in",
        "updated_at":"..."
    }
]
```

---

# Get Conversation

## GET /conversations/{id}

Returns

Entire conversation history.

---

# Delete Conversation

## DELETE /conversations/{id}

Deletes

Conversation

Messages

Associated metadata

---

# Search Documents

## POST /search

Purpose

Semantic document search without generating an answer.

Request

```json
{
    "query":"late checkout"
}
```

Response

```json
{
    "results":[]
}
```

---

# Summarize Document

## POST /documents/{id}/summary

Purpose

Generate document summary.

Response

```json
{
    "summary":"..."
}
```

---

# Compare Documents

## POST /documents/compare

Request

```json
{
    "document_one":"...",
    "document_two":"..."
}
```

Response

```json
{
    "comparison":"..."
}
```

---

# List Available Documents

## GET /documents/catalog

Purpose

Return every indexed document.

Useful for dropdowns.

---

# System Status

## GET /system/status

Purpose

Return application health.

Includes

Database

Vector Database

LLM

Disk Usage

Memory

---

# Statistics

## GET /system/stats

Returns

Documents Indexed

Chunks

Embeddings

Conversations

Messages

Average Response Time

---

# Configuration

## GET /settings

Future Feature

Returns

Chunk Size

Embedding Model

Top K

LLM Model

Temperature

---

# Update Settings

## PUT /settings

Future Feature

Allows administrators to update runtime settings.

---

# Error Codes

| Code | Meaning |
|-------|----------|
| 200 | Success |
| 201 | Created |
| 204 | Deleted Successfully |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Resource Not Found |
| 409 | Conflict |
| 413 | File Too Large |
| 422 | Validation Error |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

# Validation Rules

Uploads

Maximum Size

50 MB

Supported Formats

PDF

Markdown

Future

DOCX

TXT

---

# Rate Limiting

Future Feature

Anonymous

60 requests/hour

Authenticated

500 requests/hour

Admin

Unlimited

---

# API Versioning

Current Version

```
/api/v1/
```

Future

```
/api/v2/
```

Breaking changes should always introduce a new version.

---

# Security

All user input must be validated.

Use HTTPS in production.

Protect API keys.

Reject malicious uploads.

Prevent prompt injection.

Sanitize filenames.

Validate MIME types.

---

# Logging

Log

API Request

Execution Time

Status Code

Errors

Upload Duration

Search Duration

LLM Duration

Do not log

Passwords

API Keys

Sensitive document contents

---

# OpenAPI Documentation

FastAPI automatically exposes:

```
/docs
```

Swagger UI

and

```
/redoc
```

ReDoc Documentation

These should remain enabled during development.

---

# Future Endpoints

Authentication

```
POST /login

POST /logout

POST /refresh
```

Users

```
GET /users

POST /users

DELETE /users
```

Analytics

```
GET /analytics
```

Feedback

```
POST /feedback
```

Notifications

```
GET /notifications
```

Voice

```
POST /voice/chat
```

---

# Summary

The API provides a clean, versioned, and extensible interface for interacting with the Hospitality AI Operations Assistant. It separates concerns between the frontend, backend, AI agent, and storage systems while maintaining consistent request and response formats for future scalability.