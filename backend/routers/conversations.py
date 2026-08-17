# Chat history: list conversations, open one, create one, delete one.

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from database import conversations_collection
from models import (
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    Message,
)
from routers.subjects import to_object_id

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
def list_conversations(current_user: dict = Depends(get_current_user)):
    """Newest chat first - this fills the sidebar."""
    conversations = conversations_collection.find(
        {"user_id": current_user["id"]}
    ).sort("updated_at", -1)

    return [
        ConversationSummary(
            id=str(conversation["_id"]),
            title=conversation["title"],
            subject_id=conversation.get("subject_id"),
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"],
        )
        for conversation in conversations
    ]


@router.post("", response_model=ConversationDetail)
def create_conversation(
    data: ConversationCreate, current_user: dict = Depends(get_current_user)
):
    now = datetime.now(timezone.utc).isoformat()
    new_conversation = {
        "user_id": current_user["id"],
        "subject_id": data.subject_id,
        "title": data.title or "New Chat",
        "messages": [],
        "created_at": now,
        "updated_at": now,
    }
    result = conversations_collection.insert_one(new_conversation)

    return ConversationDetail(
        id=str(result.inserted_id),
        title=new_conversation["title"],
        subject_id=data.subject_id,
        created_at=now,
        updated_at=now,
        messages=[],
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str, current_user: dict = Depends(get_current_user)
):
    conversation = conversations_collection.find_one(
        {"_id": to_object_id(conversation_id), "user_id": current_user["id"]}
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationDetail(
        id=conversation_id,
        title=conversation["title"],
        subject_id=conversation.get("subject_id"),
        created_at=conversation["created_at"],
        updated_at=conversation["updated_at"],
        messages=[Message(**message) for message in conversation["messages"]],
    )


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str, current_user: dict = Depends(get_current_user)
):
    result = conversations_collection.delete_one(
        {"_id": to_object_id(conversation_id), "user_id": current_user["id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"message": "Conversation deleted"}
