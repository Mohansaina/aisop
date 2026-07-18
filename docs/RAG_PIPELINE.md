# RAG_PIPELINE.md

# Retrieval-Augmented Generation (RAG) Pipeline

## Overview

The Hospitality AI Operations Assistant uses a Retrieval-Augmented Generation (RAG) architecture to provide accurate, grounded, and explainable answers from internal hospitality documentation.

Unlike traditional chatbots that rely solely on a language model's training data, this system retrieves relevant information from uploaded documents before generating a response.

This approach minimizes hallucinations, improves accuracy, and ensures responses remain consistent with company policies.

---

# Objectives

The RAG pipeline is designed to:

- Retrieve relevant information from internal documents.
- Generate grounded responses using retrieved context.
- Provide document citations.
- Prevent hallucinations.
- Support large document collections.
- Allow easy addition of new documents without retraining the model.

---

# Pipeline Overview

```
                Upload Document
                       │
                       ▼
              Text Extraction
                       │
                       ▼
                Text Cleaning
                       │
                       ▼
               Document Chunking
                       │
                       ▼
            Metadata Generation
                       │
                       ▼
            Embedding Generation
                       │
                       ▼
              Store in ChromaDB
                       │
──────────────────────────────────────────

                  User Question
                       │
                       ▼
              Generate Embedding
                       │
                       ▼
           Similarity Search (Top K)
                       │
                       ▼
            Retrieve Relevant Chunks
                       │
                       ▼
              Build Prompt Context
                       │
                       ▼
                 OpenRouter LLM
                       │
                       ▼
              Generate Final Answer
                       │
                       ▼
               Return with Citations
```

---

# Step 1: Document Upload

Supported formats:

- PDF
- Markdown

Future formats:

- DOCX
- TXT
- HTML

Each uploaded document receives a unique identifier and metadata before processing begins.

---

# Step 2: Text Extraction

Purpose:

Extract readable text from uploaded documents.

For PDFs:

- Extract text page by page.
- Preserve headings where possible.
- Ignore decorative elements.

Expected output:

Clean plain text.

---

# Step 3: Text Cleaning

Before chunking, the extracted text is normalized.

Operations include:

- Remove excessive whitespace.
- Remove repeated headers and footers.
- Normalize line breaks.
- Preserve headings.
- Preserve numbered procedures.
- Preserve bullet lists.

Do not remove important operational information.

---

# Step 4: Document Chunking

Large documents cannot be embedded as a single block.

Documents are divided into smaller semantic chunks.

Recommended settings:

Chunk Size:

700–1000 characters

Overlap:

150–200 characters

Chunks should ideally end at:

- headings
- paragraphs
- procedure boundaries
- checklist boundaries

Avoid splitting sentences whenever possible.

---

# Chunk Metadata

Every chunk stores metadata including:

- Document ID
- File name
- Department
- Page number
- Section title
- Chunk index
- Upload timestamp

Example:

```json
{
  "document_id": "FD-001",
  "filename": "Front_Desk_Operations.pdf",
  "page": 18,
  "section": "Guest Check-In",
  "chunk": 42
}
```

---

# Step 5: Embedding Generation

Embedding Model

sentence-transformers/all-MiniLM-L6-v2

Purpose

Convert each chunk into a numerical vector representing its semantic meaning.

Advantages

- Fast
- Lightweight
- Good semantic quality
- Open source
- Efficient for production

---

# Step 6: Vector Storage

Technology

ChromaDB

Each record stores:

- Embedding vector
- Chunk text
- Metadata

Collection example:

```
hospitality_documents
```

Persistence should be enabled so vectors survive application restarts.

---

# Step 7: User Query Processing

When a user submits a question:

Example:

> How should an early check-in be handled?

The system:

1. Cleans the question.
2. Generates its embedding.
3. Searches ChromaDB.
4. Retrieves the most relevant chunks.

---

# Step 8: Similarity Search

The retriever performs semantic similarity search.

Default configuration:

Top K = 5

Future improvements:

- Metadata filters
- Department filters
- Hybrid search
- Re-ranking

---

# Step 9: Context Assembly

The retrieved chunks are combined into a structured context.

Example:

```
Document:
Front Desk Operations SOP

Section:
Guest Check-In

Content:
...

Document:
Reservation Management SOP

Section:
Early Arrival Policy

Content:
...
```

The context should remain within the model's token limits.

---

# Step 10: Prompt Construction

The system prompt contains:

- AI identity
- Rules
- Safety instructions
- Citation requirements

The user prompt contains:

- User question

The retrieved context is inserted between the system prompt and user prompt.

Example:

```
System Prompt

↓

Retrieved Context

↓

User Question
```

---

# Step 11: Response Generation

The LLM generates an answer using only the provided context.

The model must:

- Avoid guessing.
- Ignore outside knowledge when conflicting.
- State when information is unavailable.
- Maintain a professional tone.

---

# Step 12: Citation Generation

Every response should include citations whenever possible.

Example:

```
Source:
Front Desk Operations SOP

Section:
Guest Check-In

Page:
18
```

Future improvements:

- Clickable citations
- Highlighted passages
- Multiple source references

---

# Conversation Flow

```
User Question

↓

Embedding

↓

Similarity Search

↓

Retrieve Chunks

↓

Context Assembly

↓

OpenRouter

↓

Grounded Response

↓

Citation
```

---

# Error Handling

Possible failures include:

Missing document

Embedding failure

Vector search failure

LLM timeout

Invalid upload

For each failure:

- Log the error.
- Return a meaningful message.
- Avoid exposing internal implementation details.

---

# Performance Targets

Document upload:

<30 seconds

Embedding generation:

<5 seconds

Similarity search:

<500 milliseconds

LLM response:

<5 seconds

Overall chat response:

<6 seconds

---

# Future Enhancements

Future improvements include:

- Hybrid search (keyword + vector)
- Cross-encoder re-ranking
- Parent-child retrieval
- Multi-query retrieval
- Context compression
- Incremental indexing
- Automatic document versioning
- Knowledge graph integration
- Image and table understanding
- OCR for scanned PDFs
- Multi-language retrieval

---

# Design Principles

The RAG pipeline follows these principles:

- Ground responses in retrieved knowledge.
- Minimize hallucinations.
- Preserve document context.
- Maintain traceability through citations.
- Scale efficiently with growing document collections.
- Separate retrieval from generation.

---

# Summary

The Retrieval-Augmented Generation pipeline transforms uploaded hospitality documentation into a searchable knowledge base. By combining semantic search with a large language model, the system provides fast, accurate, and cited answers while ensuring that all responses are grounded in the organization's own operational documents.