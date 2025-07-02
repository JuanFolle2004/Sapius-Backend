# user_routes.py
from fastapi import APIRouter, HTTPException
from app.models.user import User, UserCreate, CourseProgress
from app.firebase.firebase_config import db
from uuid import uuid4
from datetime import datetime

router = APIRouter()

@router.post("/users", response_model=User)
def create_user(user: UserCreate):
    user_id = str(uuid4())

    user_dict = {
        "id": user_id,
        "email": user.email,
        "birth_date": user.birthDate.isoformat(),  # ✅ match User model field name
        "recentTopics": user.recentTopics,
        "progress": {}
    }

    db.collection("users").document(user_id).set(user_dict)

    return User(**user_dict)
