# Step 5 of RAG: build the prompt and ask GPT-4o-mini for the answer.
#
# The order every chat message goes through is:
#
#   question -> safety guardrail -> retrieval -> study guardrail -> GPT-4o-mini -> answer
#
# The retrieval happens before the study guardrail because the guardrail uses the
# search result as its first (and best) signal: if the question already matches the
# student's own notes, it is clearly about the subject.

import guardrails
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
    "Only answer study-related questions. "
    "If study material is provided, base your answer on it and mention the file name."
)

# Extra instructions used by the "Teach Me" button (tutor mode).
TEACH_INSTRUCTION = """Teach this topic to a student using exactly these four sections,
with these headings and nothing else:

**Simple Explanation**
A short, clear explanation in plain words.

**Important Points**
- three to five bullet points

**Example**
One concrete example.

**Quick Check**
One short question for the student to think about (do not answer it)."""


def build_context_block(chunks: list) -> str:
    """Join the retrieved chunks into one block of text for the prompt."""
    parts = []
    for index, chunk in enumerate(chunks, start=1):
        parts.append(f"[Extract {index} - from {chunk['filename']}]\n{chunk['text']}")
    return "\n\n".join(parts)


def retrieve_context(user_id: str, subject_id: str, question: str) -> list:
    """Similarity search inside one subject, keeping only the close-enough chunks."""
    if not subject_id:
        return []
    found = search_chunks(user_id, subject_id, question)
    return [chunk for chunk in found if chunk["distance"] <= RELEVANCE_LIMIT]


def answer_question(question, history, user_id, subject_id=None,
                    subject_name="", mode="chat"):
    """
    Returns (answer_text, used_rag, sources, status).

    status tells the frontend what happened:
      "safety"    -> blocked by the safety guardrail
      "off_topic" -> blocked by the study guardrail
      "rag"       -> answered from the uploaded study material
      "general"   -> answered from general knowledge
    """
    # ---- 1. Safety guardrail (always first) ----
    if guardrails.is_self_harm(question):
        return guardrails.SAFETY_MESSAGE, False, [], "safety"

    # ---- 2. Retrieval from this subject's documents ----
    retrieved = retrieve_context(user_id, subject_id, question)

    # ---- 3. Study guardrail ----
    if not guardrails.is_study_related(question, subject_name, retrieved):
        return guardrails.OFF_TOPIC_MESSAGE, False, [], "off_topic"

    # ---- 4. Build the prompt ----
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if mode == "teach":
        messages.append({"role": "system", "content": TEACH_INSTRUCTION})

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

    # ---- 5. GPT-4o-mini writes the answer ----
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.4,
    )
    answer = response.choices[0].message.content

    # Unique file names used for the answer, shown in the UI.
    sources = sorted({chunk["filename"] for chunk in retrieved})
    status = "rag" if retrieved else "general"
    return answer, bool(retrieved), sources, status


def make_title(first_message: str) -> str:
    """Create a short title for a new conversation from the first question."""
    title = first_message.strip().replace("\n", " ")
    if len(title) > 40:
        title = title[:40].rstrip() + "..."
    return title or "New Chat"
