# Guardrails: the two checks that run BEFORE the chatbot is allowed to answer.
#
#   1. Safety guardrail  - blocks self-harm / suicide requests.
#   2. Study guardrail   - keeps StudyMate AI focused on studying,
#                          so it does not behave like a general-purpose ChatGPT.
#
# Both are deliberately simple so they are easy to explain.

import re

from config import CHAT_MODEL
from rag.embeddings import openai_client

# ---------------------------------------------------------------------------
# 1. SAFETY GUARDRAIL
# ---------------------------------------------------------------------------

SAFETY_MESSAGE = (
    "I'm really sorry you're feeling this way. I can't help with instructions for "
    "hurting yourself. Please reach out to someone you trust or a qualified "
    "mental-health professional right now. If you may act on these thoughts soon, "
    "contact your local emergency service or go to the nearest emergency department."
)

# Phrases that clearly point to self-harm or suicide.
# We match whole phrases (not single words) so normal study questions are not blocked:
# "kill myself" matches, but "kill chain" or "terminate a TCP connection" do not.
#
# Deliberate trade-off: a few words here ("overdose") could also appear in a genuine
# medical or pharmacology question. We accept that occasional wrong refusal, because
# wrongly refusing a study question is far less harmful than wrongly answering a
# self-harm one. If StudyMate is ever used for a medical subject, this list is the
# one place to revisit.
SELF_HARM_PATTERNS = [
    r"kill myself",
    r"killing myself",
    r"kill my self",
    r"suicide",
    r"suicidal",
    r"end my life",
    r"ending my life",
    r"take my own life",
    r"want to die",
    r"wanna die",
    r"wish i was dead",
    r"wish i were dead",
    r"better off dead",
    r"don'?t want to live",
    r"do not want to live",
    r"no reason to live",
    r"hurt myself",
    r"harm myself",
    r"self[- ]harm",
    r"cut myself",
    r"cutting myself",
    r"overdose",
    r"hang myself",
]

# Compile once so the check is fast.
SELF_HARM_REGEX = re.compile("|".join(SELF_HARM_PATTERNS), re.IGNORECASE)


def is_self_harm(question: str) -> bool:
    """True if the message looks like a self-harm or suicide request."""
    return bool(SELF_HARM_REGEX.search(question))


# ---------------------------------------------------------------------------
# 2. STUDY GUARDRAIL
# ---------------------------------------------------------------------------

OFF_TOPIC_MESSAGE = (
    "I'm StudyMate, your study assistant. Please ask something related to your "
    "selected subject or uploaded study material."
)

# How close a chunk must be before we accept the question without asking the AI.
# This is STRICTER than RELEVANCE_LIMIT in rag/chain.py on purpose:
#   RELEVANCE_LIMIT (0.75) answers "is this chunk useful as context?"
#   STRONG_MATCH_LIMIT (0.55) answers "is this question definitely about the subject?"
# A loose match is not proof of relevance, so in that case we still ask GPT-4o-mini.
STRONG_MATCH_LIMIT = 0.55

# A very short prompt for the yes/no check. We ask for one word only,
# so this call is fast and cheap.
RELEVANCE_PROMPT = """You decide whether a student's question belongs in a study assistant.

Subject the student is studying: {subject}

Answer YES if the question is about learning, studying, or understanding an academic
topic that fits this subject or a closely related area of the same field.
Answer NO if it is casual chat, entertainment, cooking, poems, personal advice,
or a task unrelated to studying this subject.

Examples for the subject "Network Security":
  "What is DNS?"                     -> YES  (networking topic)
  "Explain TCP/IP."                  -> YES
  "What is the CIA triad?"           -> YES
  "Give me sample JSON for students" -> NO   (coding task, not this subject)
  "What is a Python for loop?"       -> NO   (different subject)
  "Write me a romantic poem."        -> NO
  "What is a biryani recipe?"        -> NO

Question: {question}

Answer with one word, YES or NO."""


def is_study_related(question: str, subject_name: str, retrieved_chunks: list) -> bool:
    """
    Decide whether the question is allowed through.

    Two signals, checked in order:

    1. If the similarity search found a VERY close match in the student's own
       uploaded material, the question is clearly about the subject and we let it
       through without any extra AI call. This is the RAG-based signal.

    2. Otherwise (nothing found, or only a weak match) we ask GPT-4o-mini one
       yes/no question. This is not keyword matching, so "What is DNS?" is still
       accepted for a Network Security subject even though the words do not match,
       while "What is a biryani recipe?" is refused.
    """
    best_distance = min((chunk["distance"] for chunk in retrieved_chunks), default=1.0)
    if best_distance <= STRONG_MATCH_LIMIT:
        return True

    subject = subject_name or "any academic subject the student is learning"
    prompt = RELEVANCE_PROMPT.format(subject=subject, question=question)

    try:
        response = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=3,
        )
        answer = response.choices[0].message.content.strip().upper()
        return answer.startswith("YES")
    except Exception:
        # If the check itself fails, do not block the student.
        return True
