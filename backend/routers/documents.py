# Upload study material and list / delete it.
# This is where the RAG pipeline runs when a file is uploaded.

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from auth import get_current_user
from database import documents_collection, subjects_collection
from models import DocumentResponse
from rag.loader import SUPPORTED_EXTENSIONS, extract_text
from rag.splitter import split_text
from rag.vectorstore import add_document_chunks, delete_document_chunks
from routers.subjects import to_object_id

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_FILE_MB = 10


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    subject_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    The full document pipeline:
    read file -> extract text -> split into chunks -> embed -> store in ChromaDB.
    Only the file details are saved in MongoDB, never the embeddings.
    """
    subject = subjects_collection.find_one(
        {"_id": to_object_id(subject_id), "user_id": current_user["id"]}
    )
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    if not any(file.filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
        raise HTTPException(
            status_code=400, detail="Only PDF, TXT and DOCX files are supported"
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail=f"File is larger than {MAX_FILE_MB} MB"
        )

    text = extract_text(file.filename, file_bytes)
    chunks = split_text(text)
    if not chunks:
        raise HTTPException(
            status_code=400, detail="No readable text was found in this file"
        )

    # Save the file details first so we have an id to attach to the chunks.
    record = {
        "filename": file.filename,
        "subject_id": subject_id,
        "user_id": current_user["id"],
        "upload_date": datetime.now(timezone.utc).isoformat(),
        "chunk_count": 0,
    }
    result = documents_collection.insert_one(record)
    document_id = str(result.inserted_id)

    chunk_count = add_document_chunks(
        user_id=current_user["id"],
        subject_id=subject_id,
        document_id=document_id,
        filename=file.filename,
        chunks=chunks,
    )
    documents_collection.update_one(
        {"_id": result.inserted_id}, {"$set": {"chunk_count": chunk_count}}
    )

    return DocumentResponse(
        id=document_id,
        filename=file.filename,
        subject_id=subject_id,
        chunk_count=chunk_count,
        upload_date=record["upload_date"],
    )


@router.get("/{subject_id}", response_model=list[DocumentResponse])
def list_documents(subject_id: str, current_user: dict = Depends(get_current_user)):
    documents = documents_collection.find(
        {"subject_id": subject_id, "user_id": current_user["id"]}
    ).sort("upload_date", -1)

    return [
        DocumentResponse(
            id=str(document["_id"]),
            filename=document["filename"],
            subject_id=document["subject_id"],
            chunk_count=document.get("chunk_count", 0),
            upload_date=document["upload_date"],
        )
        for document in documents
    ]


@router.delete("/{document_id}")
def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    document = documents_collection.find_one_and_delete(
        {"_id": to_object_id(document_id), "user_id": current_user["id"]}
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_chunks(document_id)
    return {"message": "Document deleted"}
