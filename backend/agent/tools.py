import sqlite3
from typing import List, Dict, Any
from backend.core.database import get_db_connection
from backend.services.vector_service import VectorService

def search_documents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search indexed documents for relevant information based on the user's natural language query.
    """
    return VectorService.search(query, limit=limit)

def list_documents() -> List[Dict[str, Any]]:
    """
    List all uploaded and indexed documents in the knowledge base.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, title, department, document_type, upload_date, status FROM documents")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_document_by_title(title: str) -> Dict[str, Any]:
    """
    Get document ID and metadata by matching its title or filename.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, filename, title, department FROM documents WHERE title LIKE ? OR filename LIKE ?", 
        (f"%{title}%", f"%{title}%")
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def retrieve_all_document_chunks(document_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all chunk texts and metadata for a specific document from ChromaDB.
    """
    collection = VectorService.get_collection()
    results = collection.get(where={"document_id": document_id})
    
    chunks = []
    if results and "documents" in results and results["documents"]:
        docs = results["documents"]
        metas = results["metadatas"]
        ids = results["ids"]
        
        for i in range(len(docs)):
            chunks.append({
                "chroma_id": ids[i],
                "text": docs[i],
                "metadata": metas[i]
            })
            
        # Sort chunks by chunk_number to preserve order
        chunks.sort(key=lambda x: x["metadata"].get("chunk_number", 0))
        
    return chunks
