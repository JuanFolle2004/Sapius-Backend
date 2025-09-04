# app/routes/progress_routes.py
from fastapi import APIRouter, Depends
from app.firebase.firebase_config import db
from app.utils.auth import get_current_user
from fastapi import Body
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/progress", tags=["Progress"])

from pydantic import BaseModel

class ProgressBody(BaseModel):
    correct: bool


@router.post("/{folder_id}/{game_id}")
def mark_game_progress(
    folder_id: str,
    game_id: str,
    body: ProgressBody = Body(...),
    current_user=Depends(get_current_user)
):
    user_id = current_user.id
    doc_ref = db.collection("users").document(user_id).collection("progress").document(folder_id)

    doc = doc_ref.get()
    data = doc.to_dict() if doc.exists else {"playedGames": {}, "strike": 0}

    played = data.get("playedGames", {})
    played[game_id] = {"correct": body.correct, "answeredAt": datetime.utcnow().isoformat()}

    # streak logic
    today = datetime.utcnow().date()
    lastPlayedAt = data.get("lastPlayedAt")
    if lastPlayedAt:
        last = datetime.fromisoformat(lastPlayedAt).date()
        data["strike"] = data.get("strike", 0) + 1 if (today - last).days == 1 else 1
    else:
        data["strike"] = 1

    data["lastPlayedAt"] = datetime.utcnow().isoformat()
    data["playedGames"] = played

    doc_ref.set(data)
    return {"success": True, "progress": data}


@router.get("/{folder_id}")
def get_folder_progress(folder_id: str, current_user=Depends(get_current_user)):
    user_id = current_user.id
    doc_ref = db.collection("users").document(user_id).collection("progress").document(folder_id)
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else {"playedGames": {}, "strike": 0}
