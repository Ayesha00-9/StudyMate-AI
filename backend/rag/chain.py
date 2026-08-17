# Step 5 of RAG: build the prompt and ask GPT-4o-mini for the answer.
# This file also contains the very simple rule that decides
# whether a question should use the uploaded study material or not.

from config import CHAT_MODEL
from rag.embeddings import openai_client
from rag.vectorstore import search_chunks

# A chunk is only useful if it is reasonably close in meaning to the question.
# With cosine distance, 0 = identical meaning and 1 = unrelated.
# Lower this number to make the search stricter.
RELEVANCE_LIMIT = 0.75

# How many previous messages we send back to the model.
# Keeping this small stops the prompt from growing forever.
HISTORY_LIMIT = 8

SYSTEM_PROMPT = (
    "You are StudyMate AI, a friendly study assistant for students. "
    "Explain topics clearly and simply, use short paragraphs and examples. "
    "If study material is provided, base your answer on it and mention the file name."
)


def build_context_block(chunks: list) -> str:
    """Join the retrieved chunks into one block of text for the prompt."""
    parts = []
    for index, chunk in enumerate(chunks, start=1):
        parts.append(f"[Extract {index} - from {chunk['filename']}]\n{chunk['text']}")
    return "\n\n".join(parts)


def answer_question(question: str, history: list, user_id: str, subject_id: str = None):
    """
    Returns (answer_text, used_rag, sources).

    Simple decision rule:
      - No subject selected  -> normal AI chat.
      - Subject selected     -> search that subject's documents.
            relevant chunks found -> answer from the documents (RAG)
            nothing relevant      -> tell the student it is not in their material,
                                     then still answer from general knowledge.
    """
    retrieved = []
    if subject_id:
        found = search_chunks(user_id, subject_id, question)
        retrieved = [c for c in found if c["distance"] <= RELEVANCE_LIMIT]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Recent conversation so the chatbot remembers what was said before.
    for message in history[-HISTORY_LIMIT:]:
        messages.append({"role": message["role"], "content": message["content"]})

    if retrieved:
        context = build_context_block(retrieved)
        messages.append(
            {
                "role": "user",
                "content": (
                    "Answer the question using the study material below.\n\n"
                    f"STUDY MATERIAL:\n{context}\n\n"
                    f"QUESTION: {question}"
                ),
            }
        )
    else:
        if subject_id:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "No matching content was found in the student's uploaded study "
                        "material. Start your reply with: 'I could not find this in your "
                        "uploaded study material, but here is a general explanation:' "
                        "and then answer normally."
                    ),
                }
            )
        messages.append({"role": "user", "content": question})

    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.4,
    )
    answer = response.choices[0].message.content

    # Unique file names used for the answer, shown in the UI.
    sources = sorted({chunk["filename"] for chunk in retrieved})
    return answer, bool(retrieved), sources


def make_title(first_message: str) -> str:
    """Create a short title for a new conversation from the first question."""
    title = first_message.strip().replace("\n", " ")
    if len(title) > 40:
        title = title[:40].rstrip() + "..."
    return title or "New Chat"
