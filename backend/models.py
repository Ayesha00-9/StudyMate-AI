# Pydantic models describe what the API accepts and what it returns.
# FastAPI uses them to validate requests automatically.

from typing import List, Optional
from pydantic import BaseModel, EmailStr


# ---------- Auth ----------

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------- Subjects ----------

class SubjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class SubjectResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    document_count: int = 0


# ---------- Documents ----------

class DocumentResponse(BaseModel):
    id: str
    filename: str
    subject_id: str
    chunk_count: int = 0
    upload_date: str


# ---------- Conversations ----------

class Message(BaseModel):
    role: str          # "user" or "assistant"
    content: str
    created_at: str


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Chat"
    subject_id: Optional[str] = None


class ConversationSummary(BaseModel):
    id: str
    title: str
    subject_id: Optional[str] = None
    created_at: str
    updated_at: str


class ConversationDetail(ConversationSummary):
    messages: List[Message] = []


# ---------- Chat ----------

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    subject_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    used_rag: bool
    sources: List[str] = []


# ---------- Dashboard ----------

class DashboardStats(BaseModel):
    total_subjects: int
    total_documents: int
    total_conversations: int
