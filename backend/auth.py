# Everything related to passwords and login tokens lives here.
# We hash passwords with bcrypt and we identify logged-in users with a JWT.

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import JWT_ALGORITHM, JWT_EXPIRE_HOURS, JWT_SECRET
from database import users_collection

# Tells FastAPI to read the "Authorization: Bearer <token>" header.
security_scheme = HTTPBearer()


def hash_password(plain_password: str) -> str:
    """Turn a plain password into a bcrypt hash. The original is never stored."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a login password against the stored hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    """Create a signed token that proves who the user is."""
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    """
    Protects a route. FastAPI runs this before the route function:
    it reads the token, checks the signature and loads the user from MongoDB.
    """
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
    )

    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
    except jwt.PyJWTError:
        raise invalid

    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        raise invalid

    if user is None:
        raise invalid

    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
    }
