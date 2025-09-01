from fastapi import APIRouter, Depends, HTTPException
from app.models.user_model import User
from app.utils.auth import get_current_user
from app.firebase.firebase_config import db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("")
def get_dashboard(current_user: User = Depends(get_current_user)):
    print("GET /dashboard for", current_user.id)

    user_doc = db.collection("users").document(current_user.id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = user_doc.to_dict()
    user_data["id"] = current_user.id

    q = db.collection("folders").where("createdBy", "==", current_user.id).stream()
    folders = []
    for doc in q:
        f = doc.to_dict()
        f["id"] = doc.id

        created_at = f.get("createdAt")
        if hasattr(created_at, "isoformat"):
            f["createdAt"] = created_at.isoformat()
        elif isinstance(created_at, dict) and created_at.get("_seconds"):
            from datetime import datetime
            f["createdAt"] = datetime.fromtimestamp(created_at["_seconds"]).isoformat()
        elif created_at is None:
            from datetime import datetime
            f["createdAt"] = datetime.utcnow().isoformat()

        f.setdefault("gameIds", [])

        folders.append(f)

    print("folders count:", len(folders))
    return {"user": user_data, "folders": folders}

