import os
import uuid
import chromadb
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from backend.core.config import settings

class VectorService:
    _model = None
    _client = None
    _collection = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """
        Lazily loads the SentenceTransformer model to speed up application startup.
        """
        if cls._model is None:
            cls._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        return cls._model

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
        """
        if cls._collection is None:
            client = cls.get_client()
            cls._collection = client.get_or_create_collection("hospitality_documents")
        return cls._collection

    @classmethod
    def add_chunks(cls, document_id: str, filename: str, department: str, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Generates embeddings for chunks and saves them in ChromaDB.
        Returns a list of chroma_ids.
        """
        collection = cls.get_collection()
        model = cls.get_model()

        texts = [chunk["text"] for chunk in chunks]
        embeddings = model.encode(texts).tolist()

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
        # ChromaDB supports filtering by metadata key during delete
        collection.delete(where={"document_id": document_id})

    @classmethod
    def search(cls, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Computes query embedding and performs a similarity search in ChromaDB.
        """
        if limit is None:
            limit = settings.TOP_K

        collection = cls.get_collection()
        model = cls.get_model()

        query_embedding = model.encode([query]).tolist()[0]
        
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
