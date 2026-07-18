import os
import uuid
import hashlib
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from backend.core.config import settings
from backend.core.database import get_db_connection
from backend.services.document_service import DocumentService
from backend.services.vector_service import VectorService

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

def process_document_background(doc_id: str, file_path: str, filename: str, department: str, doc_type: str):
    """
    Background worker that extracts text, chunks it, embeds it, and indexes it.
    """
    conn = get_db_connection()
    try:
        # Update status to processing
        conn.execute("UPDATE documents SET status = 'Processing' WHERE id = ?", (doc_id,))
        conn.commit()

        # Text extraction and chunking
        if filename.endswith(".pdf"):
            text, page_mappings = DocumentService.extract_text_from_pdf(file_path)
            chunks = DocumentService.chunk_text(text, page_mappings=page_mappings)
        else: # Markdown / Text
            text, meta = DocumentService.extract_text_from_markdown(file_path)
            chunks = DocumentService.chunk_text(text)

        if not chunks:
            raise ValueError("No text could be extracted from document.")

        # Generate embeddings and store in ChromaDB
        chroma_ids = VectorService.add_chunks(doc_id, filename, department, chunks)

        # Store chunks in SQLite
        cursor = conn.cursor()
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
        
        # Mark as Indexed
        conn.execute("UPDATE documents SET status = 'Indexed' WHERE id = ?", (doc_id,))
        conn.commit()
    except Exception as e:
        conn.execute("UPDATE documents SET status = 'Failed' WHERE id = ?", (doc_id,))
        conn.commit()
        # Record error details in uploads table
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE uploads SET upload_status = 'Failed', error_message = ?, completed_at = CURRENT_TIMESTAMP WHERE document_id = ?",
            (str(e), doc_id)
        )
        conn.commit()
    finally:
        # Update successful upload record
        cursor = conn.cursor()
        cursor.execute(
            "SELECT count(*) FROM document_chunks WHERE document_id = ?", (doc_id,)
        )
        if cursor.fetchone()[0] > 0:
            conn.execute(
                "UPDATE uploads SET upload_status = 'Completed', completed_at = CURRENT_TIMESTAMP WHERE document_id = ?",
                (doc_id,)
            )
            conn.commit()
        conn.close()

@router.post("/documents/upload")
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    department: str = Form("General"),
    document_type: str = Form("SOP")
):
    """
    Upload a new document (PDF or Markdown) to the knowledge base.
    """
    # 1. Validate file extension
    filename = os.path.basename(file.filename) # Sanitize traversal path
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".md", ".markdown"]:
        raise HTTPException(status_code=400, detail="Only PDF and Markdown (.md) files are supported.")

    # 2. Save file locally (chunked writing to prevent memory overflows)
    os.makedirs(settings.KNOWLEDGE_DIR, exist_ok=True)
    file_path = os.path.join(settings.KNOWLEDGE_DIR, filename)
    
    # Verify path sandbox boundary
    resolved_path = os.path.abspath(file_path)
    sandbox_dir = os.path.abspath(settings.KNOWLEDGE_DIR)
    if not resolved_path.startswith(sandbox_dir + os.path.sep) and resolved_path != sandbox_dir:
        raise HTTPException(status_code=400, detail="Invalid target path.")

    # Compute checksum while saving
    hasher = hashlib.sha256()
    size = 0
    with open(file_path, "wb") as f:
        while chunk := file.file.read(8192):
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                f.close()
                os.remove(file_path)
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB.")
            hasher.update(chunk)
            f.write(chunk)

    checksum = hasher.hexdigest()

    # 3. Create records in DB
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if duplicate file
    cursor.execute("SELECT id FROM documents WHERE checksum = ? OR filename = ?", (checksum, filename))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        # Delete the temp file
        os.remove(file_path)
        raise HTTPException(status_code=409, detail="Document with identical filename or content already exists.")

    doc_id = str(uuid.uuid4())
    upload_id = str(uuid.uuid4())
    title = os.path.splitext(filename)[0].replace("_", " ").title()

    cursor.execute(
        """
        INSERT INTO documents (id, filename, title, department, document_type, status, checksum)
        VALUES (?, ?, ?, ?, ?, 'Uploading', ?)
        """,
        (doc_id, filename, title, department, document_type, checksum)
    )

    cursor.execute(
        """
        INSERT INTO uploads (id, document_id, filename, upload_status)
        VALUES (?, ?, ?, 'Uploading')
        """,
        (upload_id, doc_id, filename)
    )

    conn.commit()
    conn.close()

    # 4. Schedule background ingestion
    background_tasks.add_task(
        process_document_background,
        doc_id=doc_id,
        file_path=file_path,
        filename=filename,
        department=department,
        doc_type=document_type
    )

    return {
        "success": True,
        "document_id": doc_id,
        "status": "processing"
    }

@router.get("/documents")
def get_all_documents():
    """
    List all indexed documents in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, title, department, document_type, upload_date, status FROM documents")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.get("/documents/{document_id}")
def get_document(document_id: str):
    """
    Retrieve metadata for a specific document.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, title, department, document_type, upload_date, status FROM documents WHERE id = ?", (document_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found.")
    return dict(row)

@router.delete("/documents/{document_id}")
def delete_document(document_id: str):
    """
    Delete a document and delete its vectors from ChromaDB.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM documents WHERE id = ?", (document_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found.")
    
    filename = row["filename"]
    
    # Delete from ChromaDB
    try:
        VectorService.delete_document_vectors(document_id)
    except Exception:
        pass

    # Delete local file
    file_path = os.path.join(settings.KNOWLEDGE_DIR, filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    # Delete SQLite records (cascade deletes chunks and upload records)
    cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Document deleted successfully."}

@router.post("/documents/{document_id}/reindex")
def reindex_document(document_id: str, background_tasks: BackgroundTasks):
    """
    Rebuilds the vector embeddings for an existing document.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filename, department, document_type FROM documents WHERE id = ?", (document_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found.")
        
    filename = row["filename"]
    dept = row["department"]
    doc_type = row["document_type"]
    
    # 1. Clear old Chroma vectors and SQLite chunks
    try:
        VectorService.delete_document_vectors(document_id)
    except Exception:
        pass
    cursor.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
    conn.commit()
    conn.close()

    # 2. Run background processor
    file_path = os.path.join(settings.KNOWLEDGE_DIR, filename)
    if not os.path.exists(file_path):
        # Maybe it's in the Information seeding folder
        file_path = os.path.join(settings.INFORMATION_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Original source file not found on disk to reindex.")

    background_tasks.add_task(
        process_document_background,
        doc_id=document_id,
        file_path=file_path,
        filename=filename,
        department=dept,
        doc_type=doc_type
    )

    return {"status": "processing"}
