# DATABASE_SCHEMA.md

# Database Schema

## Overview

The Hospitality AI Operations Assistant uses SQLite as its primary relational database for storing application data.

The database stores structured information such as uploaded documents, conversations, users, messages, indexing status, and system metadata.

Vector embeddings are **not stored in SQLite**. They are stored separately in ChromaDB.

---

# Database Design Principles

The database is designed to be:

- Normalized
- Lightweight
- Easy to maintain
- Production-ready
- Easily migratable to PostgreSQL

Primary keys use UUIDs.

Foreign key relationships should be enforced.

Indexes should be added on frequently queried fields.

---

# Database Overview

The application consists of the following tables:

```
Users

Documents

DocumentChunks

Conversations

Messages

Uploads

SystemSettings
```

---

# Entity Relationship Diagram

```
Users
   │
   ├──────────────┐
   │              │
   ▼              ▼

Conversations   Uploads

   │
   ▼

Messages

Documents

   │
   ▼

DocumentChunks
```

---

# Users Table

Purpose

Stores registered users.

Future feature.

Fields

| Column | Type | Description |
|---------|------|-------------|
| id | UUID | Primary Key |
| name | TEXT | Full name |
| email | TEXT | Unique email |
| password_hash | TEXT | Encrypted password |
| role | TEXT | User role |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update |

Roles

- Admin
- Manager
- Employee

---

# Documents Table

Purpose

Stores uploaded document metadata.

Fields

| Column | Type |
|---------|------|
| id | UUID |
| filename | TEXT |
| title | TEXT |
| department | TEXT |
| document_type | TEXT |
| upload_date | DATETIME |
| uploaded_by | UUID |
| total_pages | INTEGER |
| status | TEXT |
| checksum | TEXT |

Status values

- Uploading
- Processing
- Indexed
- Failed

---

# DocumentChunks Table

Purpose

Tracks document chunks.

The actual embeddings remain in ChromaDB.

Fields

| Column | Type |
|---------|------|
| id | UUID |
| document_id | UUID |
| chunk_number | INTEGER |
| page_number | INTEGER |
| section | TEXT |
| chroma_id | TEXT |
| created_at | DATETIME |

Relationship

Many chunks belong to one document.

---

# Conversations Table

Purpose

Stores chat sessions.

Fields

| Column | Type |
|---------|------|
| id | UUID |
| user_id | UUID |
| title | TEXT |
| created_at | DATETIME |
| updated_at | DATETIME |

---

# Messages Table

Purpose

Stores chat messages.

Fields

| Column | Type |
|---------|------|
| id | UUID |
| conversation_id | UUID |
| role | TEXT |
| content | TEXT |
| citations | JSON |
| created_at | DATETIME |

Role values

- User

- Assistant

---

# Uploads Table

Purpose

Tracks document upload jobs.

Fields

| Column | Type |
|---------|------|
| id | UUID |
| document_id | UUID |
| filename | TEXT |
| upload_status | TEXT |
| started_at | DATETIME |
| completed_at | DATETIME |
| error_message | TEXT |

Status

Queued

Uploading

Processing

Completed

Failed

---

# SystemSettings Table

Purpose

Stores application configuration.

Fields

| Column | Type |
|---------|------|
| key | TEXT |
| value | TEXT |

Examples

Embedding Model

Chunk Size

Chunk Overlap

Top K

LLM Model

Temperature

---

# Relationships

Users

↓

Conversations

↓

Messages

Documents

↓

DocumentChunks

Documents

↓

Uploads

---

# Indexes

Create indexes on

Documents.filename

Documents.department

DocumentChunks.document_id

Messages.conversation_id

Conversations.user_id

Uploads.document_id

---

# Constraints

Email must be unique.

Filename should be unique.

Foreign keys must be enforced.

Cascade delete messages when conversation is removed.

Cascade delete chunks when document is removed.

---

# Data Lifecycle

## Upload

Create document

↓

Process document

↓

Create chunks

↓

Store metadata

↓

Store embeddings in ChromaDB

↓

Mark indexed

---

## Chat

Create conversation

↓

Create user message

↓

Retrieve chunks

↓

Generate answer

↓

Store assistant response

---

# ChromaDB Integration

SQLite stores:

- Metadata
- Conversations
- Users
- Uploads

ChromaDB stores:

- Embeddings
- Vector IDs
- Chunk text
- Metadata

SQLite references ChromaDB using the `chroma_id` field.

---

# Migration Strategy

SQLite is used for development and MVP.

Future migration path:

SQLite

↓

PostgreSQL

↓

Managed Cloud Database

No application logic should depend on SQLite-specific behavior.

---

# Backup Strategy

Database backups should include:

Users

Documents

Conversations

Messages

Uploads

ChromaDB should be backed up separately.

---

# Performance Considerations

- Use UUID primary keys.
- Index frequently queried columns.
- Keep transactions short.
- Avoid unnecessary joins.
- Paginate large query results.
- Archive old conversations if needed.

---

# Security

Sensitive data must be protected.

Passwords should never be stored in plain text.

Store password hashes only.

Validate all user input.

Use parameterized queries.

Never build SQL using string concatenation.

---

# Future Tables

Potential future additions:

AuditLogs

Roles

Permissions

Departments

Notifications

Feedback

Analytics

APIKeys

ModelUsage

DocumentVersions

---

# Summary

The relational database stores the application's structured data while ChromaDB manages semantic vectors. This separation keeps the system modular, scalable, and easy to migrate to enterprise-grade database solutions as the project grows.