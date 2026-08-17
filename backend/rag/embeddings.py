# Step 3 of RAG: turn text into embeddings (lists of numbers that capture meaning).
# We also keep the single shared OpenAI client here.

from openai import OpenAI

from config import EMBEDDING_MODEL, OPENAI_API_KEY

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def embed_texts(texts: list) -> list:
    """Create an embedding for every chunk in the list."""
    if not texts:
        return []
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def embed_query(question: str) -> list:
    """Create an embedding for a single user question."""
    return embed_texts([question])[0]
