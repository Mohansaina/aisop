import os
import psutil
from fastapi import APIRouter
from backend.core.database import get_db_connection
from backend.services.vector_service import VectorService
from backend.core.config import settings

router = APIRouter()

@router.get("/health")
def get_health():
    """
    Returns API status and version.
    """
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

@router.get("/system/status")
def get_system_status():
    """
    Check availability of SQLite, ChromaDB, and system resource limits.
    """
    db_ok = False
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        pass

    chroma_ok = False
    try:
        VectorService.get_collection()
        chroma_ok = True
    except Exception:
        pass

    # Disk usage
    disk = psutil.disk_usage(os.path.dirname(settings.SQLITE_DB_PATH))
    memory = psutil.virtual_memory()

    return {
        "success": True,
        "data": {
            "database": "connected" if db_ok else "failed",
            "vector_database": "connected" if chroma_ok else "failed",
            "llm_provider": "configured" if settings.OPENROUTER_API_KEY else "unconfigured",
            "disk_usage_percent": disk.percent,
            "memory_usage_percent": memory.percent
        }
    }

@router.get("/system/stats")
def get_system_stats():
    """
    Retrieves knowledge statistics: document count, chunk count, conversation count.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        chunk_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        conv_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        msg_count = cursor.fetchone()[0]
        
        conn.close()
    except Exception as e:
        doc_count, chunk_count, conv_count, msg_count = 0, 0, 0, 0

    return {
        "success": True,
        "data": {
            "documents_indexed": doc_count,
            "chunks_stored": chunk_count,
            "conversations_total": conv_count,
            "messages_total": msg_count,
            "average_response_time_ms": 1200 # Static placeholder
        }
    }
