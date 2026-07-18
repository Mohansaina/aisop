import os
import uuid
import chromadb
import httpx
from typing import List, Dict, Any
from backend.core.config import settings

class VectorService:
    _model = None
    _client = None
    _collection = None

    @classmethod
    def get_client(cls) -> chromadb.PersistentClient:
        """
        Lazily gets the persistent ChromaDB client.
        """
        if cls._client is None:
            cls._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        return cls._client

    @classmethod
    def get_collection(cls) -> Any:
        """
        Gets or creates the ChromaDB collection for hospitality documents.
        Uses a separate collection name for Nvidia NIM to avoid dimension mismatch (384 vs 1024).
        """
        if cls._collection is None:
            client = cls.get_client()
            col_name = "hospitality_documents"
            if settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.startswith("nvapi-"):
                col_name = "hospitality_documents_nv"
            cls._collection = client.get_or_create_collection(col_name)
        return cls._collection

    @classmethod
    def _get_embeddings(cls, texts: List[str], input_type: str = "document") -> List[List[float]]:
        """
        Generates vector embeddings. Calls Nvidia NIM Embed API if key starts with 'nvapi-'.
        Otherwise, falls back to local SentenceTransformer (lazy loaded).
        """
        if not settings.OPENROUTER_API_KEY:
            return [[0.0] * 384] * len(texts)

        if settings.OPENROUTER_API_KEY.startswith("nvapi-"):
            try:
                headers = {
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }
                all_embeddings = []
                batch_size = 16
                # Batch processing to prevent NIM payload threshold alerts
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    payload = {
                        "input": batch,
                        "model": "nvidia/embed-qa-4",
                        "input_type": input_type,
                        "encoding_format": "float"
                    }
                    with httpx.Client(timeout=30.0) as client:
                        res = client.post(
                            "https://integrate.api.nvidia.com/v1/embeddings",
                            headers=headers,
                            json=payload
                        )
                        res.raise_for_status()
                        data = res.json()
                        # Sort by original index to preserve ordering
                        sorted_items = sorted(data["data"], key=lambda x: x["index"])
                        embeddings = [item["embedding"] for item in sorted_items]
                        all_embeddings.extend(embeddings)
                return all_embeddings
            except Exception as e:
                print(f"[VectorService] Nvidia Cloud Embedding failed: {e}. Returning zero vectors.")
                return [[0.0] * 1024] * len(texts)
        else:
            # Lazy import SentenceTransformer to prevent import crashes in environments without PyTorch
            try:
                from sentence_transformers import SentenceTransformer
                if cls._model is None:
                    cls._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                return cls._model.encode(texts).tolist()
            except ImportError:
                print("[VectorService] sentence-transformers not installed. Returning zero vectors.")
                return [[0.0] * 384] * len(texts)

    @classmethod
    def add_chunks(cls, document_id: str, filename: str, department: str, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Generates embeddings for chunks and saves them in ChromaDB.
        Returns a list of chroma_ids.
        """
        collection = cls.get_collection()
        texts = [chunk["text"] for chunk in chunks]
        
        # Call the unified embeddings generator
        embeddings = cls._get_embeddings(texts, input_type="document")

        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = []
        
        for idx, chunk in enumerate(chunks):
            metadatas.append({
                "document_id": document_id,
                "filename": filename,
                "department": department,
                "chunk_number": chunk["chunk_number"],
                "page_number": chunk.get("page_number", 1) or 1,
                "section": chunk.get("section", "General") or "General"
            })

        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts
        )
        return ids

    @classmethod
    def delete_document_vectors(cls, document_id: str) -> None:
        """
        Removes all vector embeddings associated with a specific document ID.
        """
        collection = cls.get_collection()
        collection.delete(where={"document_id": document_id})

    @classmethod
    def search(cls, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Computes query embedding and performs a similarity search in ChromaDB.
        """
        if limit is None:
            limit = settings.TOP_K

        collection = cls.get_collection()
        
        # Call the unified embeddings generator for the query
        query_embeddings = cls._get_embeddings([query], input_type="query")
        if not query_embeddings:
            return []
        query_embedding = query_embeddings[0]
        
        # Retrieve a larger pool of candidates to perform hybrid re-ranking
        candidate_limit = min(limit * 3, 20)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=candidate_limit
        )

        formatted_results = []
        if results and "documents" in results and results["documents"] and len(results["documents"][0]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]
            ids = results["ids"][0]

            # Tokenize query for term-frequency matching
            stop_words = {"what", "is", "are", "the", "for", "how", "to", "do", "we", "i", "can", "you", "tell", "me", "about", "in", "on", "at", "of", "and", "a", "an", "with"}
            query_words = [w.strip("?,.!") for w in query.lower().split()]
            query_tokens = [w for w in query_words if w and w not in stop_words]
            # Extract numbers from query to boost exact match precision
            query_numbers = [w for w in query_tokens if any(c.isdigit() for c in w)]

            for i in range(len(docs)):
                text_lower = docs[i].lower()
                
                # 1. Base semantic score
                semantic_score = 1.0 - (distances[i] / 2.0)
                
                # 2. Keyword overlap score
                keyword_matches = sum(1 for token in query_tokens if token in text_lower)
                keyword_score = keyword_matches / max(len(query_tokens), 1)

                # 3. Numeric & SOP accent boosts (important for temperature ranges and sections)
                numeric_boost = 0.0
                if query_numbers:
                    matched_numbers = sum(0.4 for num in query_numbers if num in text_lower)
                    numeric_boost += matched_numbers
                
                # Boost if filename or section matches query words
                meta = metas[i]
                meta_boost = 0.0
                if meta:
                    filename_clean = meta.get("filename", "").lower().replace("_", " ")
                    section_clean = meta.get("section", "").lower().replace("_", " ")
                    for token in query_tokens:
                        if token in filename_clean or token in section_clean:
                            meta_boost += 0.15

                hybrid_score = semantic_score + (0.35 * keyword_score) + numeric_boost + meta_boost

                formatted_results.append({
                    "chroma_id": ids[i],
                    "text": docs[i],
                    "metadata": meta,
                    "distance": distances[i],
                    "hybrid_score": hybrid_score
                })

            # Sort by the consolidated hybrid score in descending order
            formatted_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
            # Slice down to original requested limit
            formatted_results = formatted_results[:limit]

        return formatted_results
