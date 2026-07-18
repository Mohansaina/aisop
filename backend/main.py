import os
import uuid
import hashlib
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.core.database import init_db, get_db_connection
from backend.services.document_service import DocumentService
from backend.services.vector_service import VectorService
from backend.api.endpoints import health, documents, chat

def seed_information_documents():
    """
    Scans the local `Information/` directory and auto-indexes all .md files 
    into SQLite and ChromaDB on server startup.
    """
    if not os.path.exists(settings.INFORMATION_DIR):
        print(f"[Seeder] Information directory {settings.INFORMATION_DIR} does not exist. Skipping.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    files = [f for f in os.listdir(settings.INFORMATION_DIR) if f.endswith(".md")]
    print(f"[Seeder] Found {len(files)} files in Information directory.")

    for filename in files:
        file_path = os.path.join(settings.INFORMATION_DIR, filename)
        
        # Calculate checksum
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        checksum = hasher.hexdigest()

        # Check if already exists in DB
        cursor.execute("SELECT id, status FROM documents WHERE filename = ? OR checksum = ?", (filename, checksum))
        row = cursor.fetchone()
        
        if row:
            if row["status"] == "Indexed":
                print(f"[Seeder] Document '{filename}' already fully indexed. Skipping.")
                continue
            else:
                # Delete partial/failed document records to reindex
                doc_id = row["id"]
                conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                try:
                    VectorService.delete_document_vectors(doc_id)
                except Exception:
                    pass
                conn.commit()

        # Begin ingestion
        print(f"[Seeder] Ingesting and indexing '{filename}'...")
        doc_id = str(uuid.uuid4())
        title = filename.replace(".md", "").replace("_", " ").title()
        
        # Extract title and department metadata from cover page if possible
        try:
            text, meta = DocumentService.extract_text_from_markdown(file_path)
            dept = meta.get("department", "Operations")
            doc_title = meta.get("document_title", title)
        except Exception:
            text = ""
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            dept = "Operations"
            doc_title = title
            
        cursor.execute(
            """
            INSERT INTO documents (id, filename, title, department, document_type, status, checksum)
            VALUES (?, ?, ?, ?, 'Policy', 'Processing', ?)
            """,
            (doc_id, filename, doc_title, dept, checksum)
        )
        conn.commit()

        try:
            # Clean and chunk
            clean_text = DocumentService.clean_text(text)
            chunks = DocumentService.chunk_text(clean_text)
            
            if not chunks:
                raise ValueError("Seeding text extraction returned empty.")

            # Add to ChromaDB
            chroma_ids = VectorService.add_chunks(doc_id, filename, dept, chunks)

            # Insert chunk metadata
            for idx, chunk in enumerate(chunks):
                cursor.execute(
                    """
                    INSERT INTO document_chunks (id, document_id, chunk_number, page_number, section, chroma_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        doc_id,
                        chunk["chunk_number"],
                        chunk.get("page_number", 1),
                        chunk.get("section", "General"),
                        chroma_ids[idx]
                    )
                )
            
            conn.execute("UPDATE documents SET status = 'Indexed' WHERE id = ?", (doc_id,))
            conn.commit()
            print(f"[Seeder] Successfully indexed '{filename}' with {len(chunks)} chunks.")
        except Exception as e:
            conn.execute("UPDATE documents SET status = 'Failed' WHERE id = ?", (doc_id,))
            conn.commit()
            print(f"[Seeder] Failed to index '{filename}': {e}")
            
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize SQLite Database
    print("[Lifecycle] Initializing SQLite database schema...")
    init_db()
    
    # 2. Seed default Information SOP documents
    print("[Lifecycle] Seeding SOP documents from Information/ directory...")
    seed_information_documents()
    
    yield
    print("[Lifecycle] Shutting down seeder workspace...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["system"])
app.include_router(documents.router, prefix=settings.API_V1_STR, tags=["documents"])
app.include_router(chat.router, prefix=settings.API_V1_STR, tags=["chat"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Hospitality AI Operations Assistant API. Go to /api/v1/health for status."}
