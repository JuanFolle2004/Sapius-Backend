from fastapi import APIRouter, Depends
from app.models.user_model import User
from app.utils.auth import get_current_user
from app.firebase.firebase_config import db
from app.models.folder import Folder
from typing import List

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/")
def get_dashboard(current_user: User = Depends(get_current_user)):
    # get user profile
    user_doc = db.collection("users").document(current_user.id).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}

    # get folders
    folders_ref = db.collection("folders").where("createdBy", "==", current_user.id).stream()
    folders = [doc.to_dict() for doc in folders_ref]

    return {
        "user": user_data,
        "folders": folders,
    }
