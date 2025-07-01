from fastapi import APIRouter, HTTPException
from app.models.user import User
from app.firebase.firebase_config import db
from datetime import datetime

router = APIRouter()

@router.post("/")
def create_user(user: User):
    user_data = user.dict()
    db.collection("users").document(user.id).set(user_data)
    return {"message": "User created successfully"}

@router.get("/{user_id}")
def get_user(user_id: str):
    doc = db.collection("users").document(user_id).get()
    if doc.exists:
        return doc.to_dict()
    else:
        raise HTTPException(status_code=404, detail="User not found")
