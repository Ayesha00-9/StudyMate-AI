# Loads all settings from the .env file so nothing sensitive is hardcoded.

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MONGODB_URI = os.getenv("MONGODB_URI", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "studymate")

# Secret used to sign the JWT login tokens.
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# Which OpenAI models we use.
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Where ChromaDB keeps its files on disk.
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_store")

# Which frontend addresses are allowed to call this API (CORS).
#
# The value is a comma separated list, for example:
#   CORS_ORIGINS=http://localhost:5173,https://studymate-ai.vercel.app
#
# We clean every entry because a stray space or a trailing "/" makes the browser
# origin not match and the request is blocked with a confusing CORS error.
# We never use "*" here, because the frontend sends an Authorization header.
DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:5174,http://127.0.0.1:5174"   # Vite's fallback port
)


def _clean_origins(raw: str) -> list:
    origins = []
    for origin in raw.split(","):
        origin = origin.strip().rstrip("/")
        if origin:
            origins.append(origin)
    return origins


CORS_ORIGINS = _clean_origins(os.getenv("CORS_ORIGINS", "") or DEFAULT_CORS_ORIGINS)

# Social login. If these are empty the buttons are simply not used,
# and email/password login keeps working exactly as before.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID", "")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET", "")
