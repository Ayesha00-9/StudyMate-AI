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


class SocialLoginRequest(BaseModel):
    """The token the browser received from Google or Facebook."""
    token: str


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
    # Saved for AI messages so the sources are still visible when an old chat
    # is reopened. Old messages simply do not have these fields.
    sources: List[str] = []
    status: str = ""


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
    mode: str = "chat"          # "chat" or "teach" (Teach Me button)


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    used_rag: bool
    sources: List[str] = []
    status: str = "general"     # safety / off_topic / rag / general


# ---------- Dashboard ----------

class DashboardStats(BaseModel):
    total_subjects: int
    total_documents: int
    total_conversations: int


# ---------- Quiz and exam ----------

class QuizRequest(BaseModel):
    subject_id: str
    count: int = 5
    kind: str = "quiz"                  # "quiz" or "exam"
    practice_weak_topics: bool = False  # use my weak topics instead of the whole subject


class QuizQuestion(BaseModel):
    """What the student sees. The correct answer is NOT included."""
    topic: str
    question: str
    options: List[str]


class QuizResponse(BaseModel):
    quiz_id: str
    kind: str
    questions: List[QuizQuestion]
    sources: List[str] = []


class QuizSubmitRequest(BaseModel):
    # One chosen option index per question, -1 means not answered.
    answers: List[int]


class QuizResultItem(BaseModel):
    question: str
    topic: str
    options: List[str]
    your_index: int
    correct_index: int
    is_correct: bool
    explanation: str


class QuizResultResponse(BaseModel):
    score: int
    total: int
    percentage: int
    results: List[QuizResultItem]
    weak_topics: List[str] = []


# ---------- Flashcards and summary ----------

class Flashcard(BaseModel):
    front: str
    back: str


class FlashcardsResponse(BaseModel):
    cards: List[Flashcard]
    sources: List[str] = []


class SummaryResponse(BaseModel):
    summary: str
    sources: List[str] = []


# ---------- Progress ----------

class ProgressResponse(BaseModel):
    questions_asked: int
    quizzes_completed: int
    average_score: int
    total_documents: int
    weak_topics: List[str] = []
