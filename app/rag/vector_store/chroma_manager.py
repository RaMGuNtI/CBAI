import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.core.config import settings
from app.rag.chunking.chunker import DocumentChunk
from app.rag.embeddings.factory import EmbeddingFactory


class ChromaManager:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
            cls._client = chromadb.PersistentClient(
                path=str(settings.CHROMA_PERSIST_DIR),
                settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True)
            )
        return cls._client

    @classmethod
    def get_collection_name(cls, chatbot_id: str) -> str:
        # Chroma collection names must be 3-63 chars, alphanumeric or underscores/hyphens
        clean_id = chatbot_id.replace("-", "_")
        return f"bot_{clean_id}"[:60]

    @classmethod
    def get_or_create_collection(cls, chatbot_id: str):
        client = cls.get_client()
        name = cls.get_collection_name(chatbot_id)
        return client.get_or_create_collection(
            name=name,
            metadata={"chatbot_id": chatbot_id, "hnsw:space": "cosine"}
        )

    @classmethod
    def add_chunks(
        cls,
        chatbot_id: str,
        chunks: List[DocumentChunk],
        embedding_model_name: str = "all-MiniLM-L6-v2"
    ) -> int:
        if not chunks:
            return 0

        collection = cls.get_or_create_collection(chatbot_id)
        embedder = EmbeddingFactory.get_embedding_model(embedding_model_name)

        texts = [chunk.content for chunk in chunks]
        embeddings = embedder.embed_documents(texts)
        ids = [chunk.id for chunk in chunks]

        metadatas = []
        for chunk in chunks:
            clean_meta = {}
            for k, v in chunk.metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                elif v is None:
                    clean_meta[k] = ""
                else:
                    clean_meta[k] = str(v)
            metadatas.append(clean_meta)

        # Batch upsert in chunks of 200
        batch_size = 200
        for i in range(0, len(chunks), batch_size):
            collection.upsert(
                ids=ids[i:i + batch_size],
                embeddings=embeddings[i:i + batch_size],
                documents=texts[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size]
            )

        return len(chunks)

    @classmethod
    def delete_document_chunks(cls, chatbot_id: str, document_id: str):
        collection = cls.get_or_create_collection(chatbot_id)
        collection.delete(where={"document_id": document_id})

    @classmethod
    def delete_chatbot_collection(cls, chatbot_id: str):
        client = cls.get_client()
        name = cls.get_collection_name(chatbot_id)
        try:
            client.delete_collection(name=name)
        except Exception:
            pass

    @classmethod
    def query(
        cls,
        chatbot_id: str,
        query_text: str,
        top_k: int = 4,
        embedding_model_name: str = "all-MiniLM-L6-v2"
    ) -> List[Dict[str, Any]]:
        collection = cls.get_or_create_collection(chatbot_id)
        if collection.count() == 0:
            return []

        embedder = EmbeddingFactory.get_embedding_model(embedding_model_name)
        query_embedding = embedder.embed_query(query_text)

        actual_k = min(top_k, collection.count())
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_k,
            include=["documents", "metadatas", "distances"]
        )

        formatted_results = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            ids = results["ids"][0] if results.get("ids") else [f"doc_{i}" for i in range(len(docs))]

            for doc, meta, dist, chunk_id in zip(docs, metas, distances, ids):
                # Chroma cosine distance = 1 - cosine_similarity (0 means identical, 1 means orthogonal)
                # Similarity score = 1 - distance
                similarity_score = max(0.0, min(1.0, 1.0 - dist))
                formatted_results.append({
                    "id": chunk_id,
                    "content": doc,
                    "metadata": meta,
                    "distance": dist,
                    "similarity": similarity_score
                })

        return formatted_results

