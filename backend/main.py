# StudyMate AI - FastAPI application entry point.
# Run with:  uvicorn main:app --reload

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import get_current_user
from config import CORS_ORIGINS
from database import (
    conversations_collection,
    create_indexes,
    documents_collection,
    subjects_collection,
)
from models import DashboardStats
from routers import auth as auth_router
from routers import chat as chat_router
from routers import conversations as conversations_router
from routers import documents as documents_router
from routers import study as study_router
from routers import subjects as subjects_router

app = FastAPI(
    title="StudyMate AI",
    description="Your AI-powered study companion. By Ayesha Amjad Ali.",
    version="1.0.0",
)

# Allow the React frontend to call this API from a different port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_indexes()


# Small extra route used by the Dashboard page.
stats_router = APIRouter(tags=["dashboard"])


@stats_router.get("/stats", response_model=DashboardStats)
def stats(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    return DashboardStats(
        total_subjects=subjects_collection.count_documents({"user_id": user_id}),
        total_documents=documents_collection.count_documents({"user_id": user_id}),
        total_conversations=conversations_collection.count_documents(
            {"user_id": user_id}
        ),
    )


app.include_router(auth_router.router)
app.include_router(subjects_router.router)
app.include_router(documents_router.router)
app.include_router(conversations_router.router)
app.include_router(chat_router.router)
app.include_router(study_router.router)
app.include_router(stats_router)


@app.get("/")
def root():
    return {"message": "StudyMate AI API is running", "docs": "/docs"}
