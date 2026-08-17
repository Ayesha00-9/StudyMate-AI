# Create, list and delete subjects. Every subject belongs to one user.

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from database import documents_collection, subjects_collection
from models import SubjectCreate, SubjectResponse
from rag.vectorstore import delete_subject_chunks

router = APIRouter(prefix="/subjects", tags=["subjects"])


def to_object_id(value: str):
    """Convert a string id from the URL into a MongoDB ObjectId."""
    try:
        return ObjectId(value)
    except InvalidId:
        raise HTTPException(status_code=404, detail="Not found")


@router.get("", response_model=list[SubjectResponse])
def list_subjects(current_user: dict = Depends(get_current_user)):
    subjects = subjects_collection.find({"user_id": current_user["id"]}).sort("name", 1)

    result = []
    for subject in subjects:
        subject_id = str(subject["_id"])
        count = documents_collection.count_documents({"subject_id": subject_id})
        result.append(
            SubjectResponse(
                id=subject_id,
                name=subject["name"],
                description=subject.get("description", ""),
                document_count=count,
            )
        )
    return result


@router.post("", response_model=SubjectResponse)
def create_subject(data: SubjectCreate, current_user: dict = Depends(get_current_user)):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Subject name is required")

    new_subject = {
        "name": name,
        "description": (data.description or "").strip(),
        "user_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = subjects_collection.insert_one(new_subject)

    return SubjectResponse(
        id=str(result.inserted_id),
        name=name,
        description=new_subject["description"],
        document_count=0,
    )


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(subject_id: str, current_user: dict = Depends(get_current_user)):
    subject = subjects_collection.find_one(
        {"_id": to_object_id(subject_id), "user_id": current_user["id"]}
    )
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    count = documents_collection.count_documents({"subject_id": subject_id})
    return SubjectResponse(
        id=subject_id,
        name=subject["name"],
        description=subject.get("description", ""),
        document_count=count,
    )


@router.delete("/{subject_id}")
def delete_subject(subject_id: str, current_user: dict = Depends(get_current_user)):
    """Deleting a subject also removes its documents and their vectors."""
    subject = subjects_collection.find_one_and_delete(
        {"_id": to_object_id(subject_id), "user_id": current_user["id"]}
    )
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    documents_collection.delete_many({"subject_id": subject_id})
    delete_subject_chunks(subject_id)

    return {"message": "Subject deleted"}
