# Quiz, flashcards and summary generation.
#
# All three do the same simple thing:
#   1. take some chunks of the student's uploaded study material (from ChromaDB)
#   2. put them in a prompt
#   3. ask GPT-4o-mini for JSON
#   4. return the JSON to the router
#
# Asking for JSON (response_format="json_object") means we get data we can use
# directly instead of text we would have to parse ourselves.

import json

from config import CHAT_MODEL
from rag.embeddings import openai_client
from rag.vectorstore import get_subject_chunks, search_chunks


def _material_text(chunks: list, max_characters: int = 9000):
    """
    Join chunks into one block of study material, with a size limit.

    Returns (text, used_chunks). We return the chunks that actually fitted so the
    "Source:" list only ever names files that really went into the prompt -
    otherwise we would tell the student an answer came from a file we never read.
    """
    parts = []
    used = []
    total = 0
    for chunk in chunks:
        piece = f"[from {chunk['filename']}]\n{chunk['text']}"
        if total + len(piece) > max_characters:
            continue  # skip this one, a later chunk may still fit
        parts.append(piece)
        used.append(chunk)
        total += len(piece)
    return "\n\n".join(parts), used


def _source_names(chunks: list) -> list:
    """The file names the material came from, shown to the student."""
    return sorted({chunk["filename"] for chunk in chunks})


def _ask_for_json(prompt: str) -> dict:
    """One GPT-4o-mini call that must reply with a JSON object."""
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def collect_material(user_id: str, subject_id: str, topics: list = None) -> list:
    """
    Get the study material to work from.

    Normally we take a general sample of the subject's chunks.
    If weak topics are given (the "Practice Weak Topics" button), we use the
    existing similarity search so the material focuses on those topics.
    """
    if topics:
        chunks = []
        seen = set()
        for topic in topics:
            for chunk in search_chunks(user_id, subject_id, topic, top_k=3):
                if chunk["text"] not in seen:
                    seen.add(chunk["text"])
                    chunks.append(chunk)
        if chunks:
            return chunks

    return get_subject_chunks(user_id, subject_id, limit=12)


# ---------------------------------------------------------------------------
# Quiz / exam questions
# ---------------------------------------------------------------------------

QUIZ_PROMPT = """You are making a multiple-choice quiz for a student, using ONLY the
study material below. Do not use outside knowledge.

STUDY MATERIAL:
{material}

Write exactly {count} questions. Reply with JSON in this exact shape:

{{"questions": [
  {{"topic": "short topic name",
    "question": "the question text",
    "options": ["option A", "option B", "option C", "option D"],
    "correct_index": 0,
    "explanation": "one short sentence explaining the correct answer"}}
]}}

Rules:
- exactly four options per question
- correct_index is 0, 1, 2 or 3
- "topic" is two or three words, so weak areas can be grouped later
- questions must be answerable from the study material above"""


def generate_quiz(user_id: str, subject_id: str, count: int = 5, topics: list = None):
    """Returns (questions, sources). Each question keeps its correct answer."""
    chunks = collect_material(user_id, subject_id, topics)
    if not chunks:
        return [], []

    material, used_chunks = _material_text(chunks)
    data = _ask_for_json(QUIZ_PROMPT.format(material=material, count=count))

    questions = []
    for item in data.get("questions", []):
        options = item.get("options", [])
        if len(options) != 4:
            continue  # skip anything malformed
        questions.append(
            {
                "topic": item.get("topic", "General"),
                "question": item.get("question", ""),
                "options": options,
                "correct_index": int(item.get("correct_index", 0)) % 4,
                "explanation": item.get("explanation", ""),
            }
        )

    return questions, _source_names(used_chunks)


# ---------------------------------------------------------------------------
# Flashcards
# ---------------------------------------------------------------------------

FLASHCARD_PROMPT = """Make study flashcards from ONLY the study material below.

STUDY MATERIAL:
{material}

Write exactly {count} flashcards. Reply with JSON in this exact shape:

{{"cards": [{{"front": "a short question or term", "back": "a short answer"}}]}}

Keep the back of each card to one or two sentences."""


def generate_flashcards(user_id: str, subject_id: str, count: int = 8):
    """Returns (cards, sources)."""
    chunks = collect_material(user_id, subject_id)
    if not chunks:
        return [], []

    material, used_chunks = _material_text(chunks)
    data = _ask_for_json(FLASHCARD_PROMPT.format(material=material, count=count))

    cards = [
        {"front": card.get("front", ""), "back": card.get("back", "")}
        for card in data.get("cards", [])
        if card.get("front") and card.get("back")
    ]
    return cards, _source_names(used_chunks)


# ---------------------------------------------------------------------------
# Study summary
# ---------------------------------------------------------------------------

SUMMARY_PROMPT = """Write a study summary using ONLY the study material below.
Do not add facts that are not in the material.

STUDY MATERIAL:
{material}

Use exactly these four markdown headings, in this order:

## Main Concepts
## Important Definitions
## Key Points
## Exam-Focused Notes

Use short bullet points under each heading."""


def generate_summary(user_id: str, subject_id: str):
    """Returns (summary_markdown, sources)."""
    chunks = collect_material(user_id, subject_id)
    if not chunks:
        return "", []

    material, used_chunks = _material_text(chunks)
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": SUMMARY_PROMPT.format(material=material)}],
        temperature=0.3,
    )
    return response.choices[0].message.content, _source_names(used_chunks)
