# The main chat route. This is what the Chat page calls on every message.

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from database import conversations_collection
from models import ChatRequest, ChatResponse
from rag.chain import answer_question, make_title
from routers.subjects import to_object_id

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    1. Find (or create) the conversation.
    2. Ask the AI, using RAG if a subject is selected.
    3. Save both messages in MongoDB.
    """
    question = data.message.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    now = datetime.now(timezone.utc).isoformat()

    # --- 1. get the conversation ---
    if data.conversation_id:
        conversation = conversations_collection.find_one(
            {"_id": to_object_id(data.conversation_id), "user_id": current_user["id"]}
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        new_conversation = {
            "user_id": current_user["id"],
            "subject_id": data.subject_id,
            "title": make_title(question),
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        inserted = conversations_collection.insert_one(new_conversation)
        new_conversation["_id"] = inserted.inserted_id
        conversation = new_conversation

    conversation_id = str(conversation["_id"])

    # The subject sent with the message wins, otherwise use the conversation's subject.
    subject_id = data.subject_id or conversation.get("subject_id")

    # --- 2. ask the AI ---
    try:
        answer, used_rag, sources = answer_question(
            question=question,
            history=conversation["messages"],
            user_id=current_user["id"],
            subject_id=subject_id,
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"AI error: {error}")

    # --- 3. save the conversation ---
    user_message = {"role": "user", "content": question, "created_at": now}
    ai_message = {
        "role": "assistant",
        "content": answer,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    update = {
        "$push": {"messages": {"$each": [user_message, ai_message]}},
        "$set": {"updated_at": ai_message["created_at"], "subject_id": subject_id},
    }
    # If this was the first message, give the chat a proper title.
    if not conversation["messages"]:
        update["$set"]["title"] = make_title(question)

    conversations_collection.update_one({"_id": ObjectId(conversation_id)}, update)

    return ChatResponse(
        answer=answer,
        conversation_id=conversation_id,
        used_rag=used_rag,
        sources=sources,
    )
