# Register / login / current user routes,
# plus "Continue with Google" and "Continue with Facebook".

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException

from auth import create_access_token, get_current_user, hash_password, verify_password
from config import (
    FACEBOOK_CLIENT_ID,
    FACEBOOK_CLIENT_SECRET,
    GOOGLE_CLIENT_ID,
)
from database import users_collection
from models import (
    LoginRequest,
    RegisterRequest,
    SocialLoginRequest,
    TokenResponse,
    UserResponse,
)

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

    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Accounts created through Google or Facebook have no password.
    if not user.get("password_hash"):
        provider = user.get("auth_provider", "social")
        raise HTTPException(
            status_code=401,
            detail=f"This account was created with {provider}. Please use that button to sign in.",
        )

    if not verify_password(data.password, user["password_hash"]):
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


# ---------------------------------------------------------------------------
# Social login (Google and Facebook)
#
# The browser talks to Google/Facebook and gets a token.
# It sends ONLY that token to us. We check the token with the provider,
# find or create the user in MongoDB, and then return OUR OWN JWT.
# From that point on everything works exactly like email/password login.
#
# The client secret never leaves the backend.
# ---------------------------------------------------------------------------

def find_or_create_social_user(provider: str, provider_id: str, name: str, email: str):
    """
    Look the student up by email so signing in with Google and then with
    email/password does not create two accounts. If there is no match, create one.
    """
    email = (email or "").lower().strip()

    user = None
    if email:
        user = users_collection.find_one({"email": email})
    if user is None:
        user = users_collection.find_one({"provider_id": provider_id})

    if user is not None:
        # Remember which provider was used (helps with a nicer login error later).
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"auth_provider": provider, "provider_id": provider_id}},
        )
        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
        }

    new_user = {
        "name": name or "Student",
        "email": email or f"{provider}_{provider_id}@studymate.local",
        "password_hash": None,          # social accounts have no password
        "auth_provider": provider,
        "provider_id": provider_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = users_collection.insert_one(new_user)

    return {
        "id": str(result.inserted_id),
        "name": new_user["name"],
        "email": new_user["email"],
    }


def social_token_response(user: dict) -> TokenResponse:
    """Same JWT as normal login - social login does not replace our auth."""
    return TokenResponse(
        access_token=create_access_token(user["id"]),
        user=UserResponse(**user),
    )


@router.post("/google", response_model=TokenResponse)
def google_login(data: SocialLoginRequest):
    """
    The frontend sends the ID token from Google Identity Services.
    We ask Google to verify it and tell us who the user is.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google login is not configured")

    try:
        response = httpx.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": data.token},
            timeout=10,
        )
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Could not reach Google")

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    info = response.json()

    # The token must have been issued for OUR app.
    if info.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="This Google token is not for this app")

    user = find_or_create_social_user(
        provider="google",
        provider_id=info.get("sub", ""),
        name=info.get("name", ""),
        email=info.get("email", ""),
    )
    return social_token_response(user)


@router.post("/facebook", response_model=TokenResponse)
def facebook_login(data: SocialLoginRequest):
    """
    The frontend sends the access token from the Facebook login popup.
    We check it with Facebook using our app secret, then read the profile.
    """
    if not FACEBOOK_CLIENT_ID or not FACEBOOK_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Facebook login is not configured")

    app_token = f"{FACEBOOK_CLIENT_ID}|{FACEBOOK_CLIENT_SECRET}"

    # Step 1: is this token real, and was it issued for our app?
    try:
        check = httpx.get(
            "https://graph.facebook.com/debug_token",
            params={"input_token": data.token, "access_token": app_token},
            timeout=10,
        ).json()
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Could not reach Facebook")

    details = check.get("data", {})
    if not details.get("is_valid") or str(details.get("app_id")) != str(FACEBOOK_CLIENT_ID):
        raise HTTPException(status_code=401, detail="Invalid Facebook token")

    # Step 2: who is it?
    try:
        profile = httpx.get(
            "https://graph.facebook.com/me",
            params={"fields": "id,name,email", "access_token": data.token},
            timeout=10,
        ).json()
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Could not reach Facebook")

    if "id" not in profile:
        raise HTTPException(status_code=401, detail="Could not read the Facebook profile")

    user = find_or_create_social_user(
        provider="facebook",
        provider_id=profile["id"],
        name=profile.get("name", ""),
        email=profile.get("email", ""),   # Facebook does not always give an email
    )
    return social_token_response(user)
