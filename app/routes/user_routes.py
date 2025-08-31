from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List
from uuid import uuid4
from datetime import datetime

from google.cloud import firestore

from app.services.generation import generate_games_from_prompt
from app.models.user_model import User
from app.models.user import UserCreate
from app.firebase.firebase_config import db
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter()

# ---------------------------
# Helper: normalized error response (root-level)
# ---------------------------
def http_error(status: int, field: str, message: str) -> JSONResponse:
    """
    Always return errors in the root:
    { "errors": [ { "field": "<field>", "message": "<message>" } ] }
    """
    return JSONResponse(
        status_code=status,
        content={"errors": [{"field": field, "message": message}]},
    )

# ---------------------------
# REGISTER
# ---------------------------
@router.post("/register", response_model=User)
def create_user(user: UserCreate):
    print("✅ Reached backend register route")
    print("📥 Incoming user data:", user.dict())

    # check if email already exists
    existing_user = db.collection("users").where("email", "==", user.email).get()
    if existing_user:
        # 409 Conflict + normalized error body at root
        return http_error(409, "email", "Email already registered")

    user_id = str(uuid4())
    hashed = hash_password(user.password)

    user_dict = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "lastname": user.lastname,
        "phone": user.phone,
        "birthDate": user.birthDate.isoformat(),
        "recentTopics": [],
        "progress": {},
        "hashed_password": hashed,
        "interests": user.interests or [],
    }

    db.collection("users").document(user_id).set(user_dict)
    return User(**user_dict)

# ---------------------------
# LOGIN
# ---------------------------
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    query = (
        db.collection("users")
        .where("email", "==", form_data.username)
        .limit(1)
        .stream()
    )
    user_doc = next(query, None)

    if not user_doc:
        return http_error(401, "email", "Invalid email or password")

    user_data = user_doc.to_dict()

    if not verify_password(form_data.password, user_data["hashed_password"]):
        return http_error(401, "password", "Invalid email or password")

    token = create_access_token(
        {
            "sub": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "lastName": user_data["lastname"],
        }
    )

    return {"access_token": token, "token_type": "bearer"}

# ---------------------------
# GET CURRENT USER
# ---------------------------
@router.get("/users/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user)):
    doc_ref = db.collection("users").document(current_user.id).get()
    if not doc_ref.exists:
        return http_error(404, "user", "User not found")

    data = doc_ref.to_dict()
    if "interests" not in data:
        data["interests"] = []
    return User(**data)

# ---------------------------
# UPDATE INTERESTS
# ---------------------------
class InterestsUpdate(BaseModel):
    interests: List[str] = Field(..., min_items=5, max_items=5)

@router.put("/users/me/interests", response_model=User)
def update_interests(
    payload: InterestsUpdate,
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id
    doc_ref = db.collection("users").document(user_id)

    if not doc_ref.get().exists:
        return http_error(404, "user", "User not found")

    # ✅ Save exactly 5 interests
    doc_ref.update({"interests": payload.interests})
    updated_user = doc_ref.get().to_dict()

    # ✅ If no folders, generate one based on first interest
    has_folders = (
        db.collection("folders").where("createdBy", "==", user_id).limit(1).get()
    )
    if not has_folders:
        first_interest = payload.interests[0]
        generated = generate_games_from_prompt(first_interest)

        folder_id = str(uuid4())
        folder_data = {
            "id": folder_id,
            "title": f"Intro to {first_interest}",
            "description": f"AI-generated quiz on {first_interest}",
            "prompt": first_interest,
            "createdBy": user_id,
            "createdAt": datetime.utcnow().isoformat(),
            "gameIds": [],
        }
        db.collection("folders").document(folder_id).set(folder_data)

        for i, g in enumerate(generated):
            game_id = str(uuid4())
            game_data = {
                "id": game_id,
                "folderId": folder_id,
                "createdBy": user_id,
                "createdAt": datetime.utcnow().isoformat(),
                "order": i + 1,
                "question": g["question"],
                "options": g["options"],
                "correctAnswer": g["correctAnswer"],
                "explanation": g["explanation"],
                "title": g["question"][:30],
                "topic": g.get("topic", first_interest),
                "tags": [g.get("topic", first_interest)],
            }
            db.collection("games").document(game_id).set(game_data)
            db.collection("folders").document(folder_id).update(
                {"gameIds": firestore.ArrayUnion([game_id])}
            )

    if "interests" not in updated_user:
        updated_user["interests"] = []

    return User(**updated_user)
