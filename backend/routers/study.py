# Study tools: quiz, exam, flashcards, summary, progress and weak topics.
# All of them reuse the existing RAG pipeline - nothing new was invented here.

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from database import (
    conversations_collection,
    documents_collection,
    quizzes_collection,
    subjects_collection,
)
from models import (
    Flashcard,
    FlashcardsResponse,
    ProgressResponse,
    QuizQuestion,
    QuizRequest,
    QuizResponse,
    QuizResultItem,
    QuizResultResponse,
    QuizSubmitRequest,
    SummaryResponse,
)
from rag.study_tools import generate_flashcards, generate_quiz, generate_summary
from routers.subjects import to_object_id

router = APIRouter(prefix="/study", tags=["study"])

NO_MATERIAL = "This subject has no uploaded study material yet. Upload a file first."


def check_subject(subject_id: str, user_id: str):
    """Make sure the subject exists and belongs to this user."""
    subject = subjects_collection.find_one(
        {"_id": to_object_id(subject_id), "user_id": user_id}
    )
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


def find_weak_topics(user_id: str, limit: int = 5) -> list:
    """
    Topics the student got wrong most often in past quizzes and exams.
    We simply count the wrong answers per topic.
    """
    wrong_counts = {}

    for quiz in quizzes_collection.find({"user_id": user_id, "submitted": True}):
        for question, chosen in zip(quiz["questions"], quiz.get("answers", [])):
            if chosen != question["correct_index"]:
                topic = question.get("topic", "General")
                wrong_counts[topic] = wrong_counts.get(topic, 0) + 1

    # Most-missed topic first.
    ordered = sorted(wrong_counts.items(), key=lambda pair: pair[1], reverse=True)
    return [topic for topic, _count in ordered[:limit]]


# ---------------------------------------------------------------------------
# Quiz and exam (same code, only the label differs)
# ---------------------------------------------------------------------------

@router.post("/quiz", response_model=QuizResponse)
def create_quiz(data: QuizRequest, current_user: dict = Depends(get_current_user)):
    """
    Generate questions from the subject's uploaded material and save them.
    The correct answers stay in MongoDB and are NOT sent to the browser,
    so the student cannot see them before submitting.
    """
    check_subject(data.subject_id, current_user["id"])

    count = max(1, min(data.count, 10))  # keep it between 1 and 10

    topics = find_weak_topics(current_user["id"]) if data.practice_weak_topics else None

    try:
        questions, sources = generate_quiz(
            user_id=current_user["id"],
            subject_id=data.subject_id,
            count=count,
            topics=topics,
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"AI error: {error}")

    if not questions:
        raise HTTPException(status_code=400, detail=NO_MATERIAL)

    record = {
        "user_id": current_user["id"],
        "subject_id": data.subject_id,
        "kind": data.kind,
        "questions": questions,      # includes correct_index and explanation
        "sources": sources,
        "answers": [],
        "score": 0,
        "submitted": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = quizzes_collection.insert_one(record)

    return QuizResponse(
        quiz_id=str(result.inserted_id),
        kind=data.kind,
        sources=sources,
        # Only topic, question and options go to the frontend.
        questions=[
            QuizQuestion(
                topic=question["topic"],
                question=question["question"],
                options=question["options"],
            )
            for question in questions
        ],
    )


@router.post("/quiz/{quiz_id}/submit", response_model=QuizResultResponse)
def submit_quiz(
    quiz_id: str,
    data: QuizSubmitRequest,
    current_user: dict = Depends(get_current_user),
):
    """Mark the answers, save the result and show what went wrong."""
    quiz = quizzes_collection.find_one(
        {"_id": to_object_id(quiz_id), "user_id": current_user["id"]}
    )
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = quiz["questions"]
    if len(data.answers) != len(questions):
        raise HTTPException(status_code=400, detail="Please answer every question")

    score = 0
    results = []
    wrong_topics = []

    for question, chosen in zip(questions, data.answers):
        is_correct = chosen == question["correct_index"]
        if is_correct:
            score += 1
        else:
            wrong_topics.append(question["topic"])

        results.append(
            QuizResultItem(
                question=question["question"],
                topic=question["topic"],
                options=question["options"],
                your_index=chosen,
                correct_index=question["correct_index"],
                is_correct=is_correct,
                explanation=question["explanation"],
            )
        )

    quizzes_collection.update_one(
        {"_id": ObjectId(quiz_id)},
        {
            "$set": {
                "answers": data.answers,
                "score": score,
                "submitted": True,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    total = len(questions)
    return QuizResultResponse(
        score=score,
        total=total,
        percentage=round(score * 100 / total) if total else 0,
        results=results,
        # Weak topics from this attempt, without repeats.
        weak_topics=sorted(set(wrong_topics)),
    )


# ---------------------------------------------------------------------------
# Flashcards and summary
# ---------------------------------------------------------------------------

@router.get("/flashcards", response_model=FlashcardsResponse)
def flashcards(
    subject_id: str,
    count: int = 8,
    current_user: dict = Depends(get_current_user),
):
    check_subject(subject_id, current_user["id"])

    try:
        cards, sources = generate_flashcards(
            current_user["id"], subject_id, max(1, min(count, 15))
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"AI error: {error}")

    if not cards:
        raise HTTPException(status_code=400, detail=NO_MATERIAL)

    return FlashcardsResponse(
        cards=[Flashcard(**card) for card in cards], sources=sources
    )


@router.get("/summary", response_model=SummaryResponse)
def summary(subject_id: str, current_user: dict = Depends(get_current_user)):
    check_subject(subject_id, current_user["id"])

    try:
        text, sources = generate_summary(current_user["id"], subject_id)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"AI error: {error}")

    if not text:
        raise HTTPException(status_code=400, detail=NO_MATERIAL)

    return SummaryResponse(summary=text, sources=sources)


# ---------------------------------------------------------------------------
# Progress and weak topics
# ---------------------------------------------------------------------------

@router.get("/progress", response_model=ProgressResponse)
def progress(current_user: dict = Depends(get_current_user)):
    """
    Simple numbers for the dashboard. Everything is filtered by user_id,
    so one student can never see another student's progress.
    """
    user_id = current_user["id"]

    # Count how many messages this student has sent.
    questions_asked = 0
    for conversation in conversations_collection.find({"user_id": user_id}):
        for message in conversation.get("messages", []):
            if message["role"] == "user":
                questions_asked += 1

    # Scores of the quizzes that were actually submitted.
    finished = list(quizzes_collection.find({"user_id": user_id, "submitted": True}))
    percentages = [
        round(quiz["score"] * 100 / len(quiz["questions"]))
        for quiz in finished
        if quiz["questions"]
    ]
    average = round(sum(percentages) / len(percentages)) if percentages else 0

    return ProgressResponse(
        questions_asked=questions_asked,
        quizzes_completed=len(finished),
        average_score=average,
        total_documents=documents_collection.count_documents({"user_id": user_id}),
        weak_topics=find_weak_topics(user_id),
    )
