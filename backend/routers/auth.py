# Register / login / current user routes.

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from auth import create_access_token, get_current_user, hash_password, verify_password
from database import users_collection
from models import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest):
    """Create a new account and log the user in straight away."""
    email = data.email.lower().strip()

    if users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="This email is already registered")

    if len(data.password) < 6:
        raise HTTPException(
            status_code=400, detail="Password must be at least 6 characters"
        )

    new_user = {
        "name": data.name.strip(),
        "email": email,
        "password_hash": hash_password(data.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = users_collection.insert_one(new_user)
    user_id = str(result.inserted_id)

    return TokenResponse(
        access_token=create_access_token(user_id),
        user=UserResponse(id=user_id, name=new_user["name"], email=email),
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    """Check the email + password and return a token."""
    email = data.email.lower().strip()
    user = users_collection.find_one({"email": email})

    if user is None or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    user_id = str(user["_id"])
    return TokenResponse(
        access_token=create_access_token(user_id),
        user=UserResponse(id=user_id, name=user["name"], email=user["email"]),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: dict = Depends(get_current_user)):
    """Used by the frontend to check that a saved token is still valid."""
    return UserResponse(**current_user)


# Logout is handled on the frontend by deleting the saved token,
# so there is no server state to clear. This route exists for completeness.
@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Logged out"}
