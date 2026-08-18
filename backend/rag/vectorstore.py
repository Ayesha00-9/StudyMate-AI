# Step 4 of RAG: store the chunks + embeddings in ChromaDB and search them later.
# Every chunk carries the user_id, subject_id and filename as metadata,
# so one subject can never see another subject's documents.

import os

# Turn off ChromaDB's usage statistics before importing it (keeps the logs clean).
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import chromadb  # noqa: E402

from config import CHROMA_DIR  # noqa: E402
from rag.embeddings import embed_query, embed_texts

# A persistent client writes the vectors to disk so they survive a restart.
chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=chromadb.config.Settings(anonymized_telemetry=False),
)
# "cosine" means the distance is 0 for identical meaning and close to 1 for unrelated text.
collection = chroma_client.get_or_create_collection(
    name="study_material",
    metadata={"hnsw:space": "cosine"},
)


def add_document_chunks(user_id: str, subject_id: str, document_id: str,
                        filename: str, chunks: list) -> int:
    """Embed the chunks and save them in ChromaDB. Returns how many were saved."""
    if not chunks:
        return 0

    vectors = embed_texts(chunks)
    ids = [f"{document_id}_{index}" for index in range(len(chunks))]
    metadatas = [
        {
            "user_id": user_id,
            "subject_id": subject_id,
            "document_id": document_id,
            "filename": filename,
        }
        for _ in chunks
    ]

    collection.add(ids=ids, documents=chunks, embeddings=vectors, metadatas=metadatas)
    return len(chunks)


def search_chunks(user_id: str, subject_id: str, question: str, top_k: int = 4):
    """
    Similarity search: find the chunks that are closest in meaning to the question,
    but only inside this user's chosen subject.
    """
    question_vector = embed_query(question)

    results = collection.query(
        query_embeddings=[question_vector],
        n_results=top_k,
        where={"$and": [{"user_id": user_id}, {"subject_id": subject_id}]},
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    found = []
    for text, meta, distance in zip(documents, metadatas, distances):
        found.append(
            {
                "text": text,
                "filename": meta.get("filename", "document"),
                "distance": distance,
            }
        )
    return found


def get_subject_chunks(user_id: str, subject_id: str, limit: int = 12) -> list:
    """
    Get some of a subject's stored chunks without asking a question.

    The quiz, flashcard and summary features need a general sample of the study
    material rather than an answer to one question, so they use this instead of
    the similarity search.
    """
    results = collection.get(
        where={"$and": [{"user_id": user_id}, {"subject_id": subject_id}]},
        limit=limit,
        include=["documents", "metadatas"],
    )

    documents = results.get("documents", []) or []
    metadatas = results.get("metadatas", []) or []

    chunks = []
    for text, meta in zip(documents, metadatas):
        chunks.append({"text": text, "filename": meta.get("filename", "document")})
    return chunks


def delete_document_chunks(document_id: str):
    """Remove one document's chunks (used when a document or subject is deleted)."""
    collection.delete(where={"document_id": document_id})


def delete_subject_chunks(subject_id: str):
    collection.delete(where={"subject_id": subject_id})
