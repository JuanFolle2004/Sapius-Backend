from fastapi import APIRouter, Depends, HTTPException
from app.models.user_model import User
from app.utils.auth import get_current_user
from app.firebase.firebase_config import db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("")   # ✅ now endpoint = /dashboard (no redirect)
def get_dashboard(current_user: User = Depends(get_current_user)):
    # get user profile
    user_doc = db.collection("users").document(current_user.id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = user_doc.to_dict()

    # get folders created by this user
    folders_ref = db.collection("folders").where("createdBy", "==", current_user.id).stream()
    folders = []
    for doc in folders_ref:
        f = doc.to_dict()
        f["id"] = doc.id   # ✅ always return folder id
        folders.append(f)

    return {
        "user": user_data,
        "folders": folders,
    }
