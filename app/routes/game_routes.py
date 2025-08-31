from fastapi import APIRouter, Depends, HTTPException
from app.models.game import Game
from app.models.user_model import User
from app.utils.auth import get_current_user
from app.firebase.firebase_config import db
from google.cloud import firestore
from uuid import uuid4
from datetime import datetime
from typing import List

router = APIRouter(prefix="/games", tags=["Games"])

@router.post("/{game_id}/mark-played")
def mark_game_played(game_id: str, current_user: User = Depends(get_current_user)):
    user_ref = db.collection("users").document(current_user.id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Append gameId to playedGameIds
    user_ref.update({
        "playedGameIds": firestore.ArrayUnion([game_id])
    })

    return {"message": f"Game {game_id} marked as played"}


@router.get("/{game_id}", response_model=Game)
def get_game_by_id(game_id: str, user: User = Depends(get_current_user)):
    try:
        doc = db.collection("games").document(game_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Game not found")

        data = doc.to_dict()
        data["id"] = doc.id

        # ✅ Allow access if it's a "random trivia" game
        if data.get("folderId") != "random":
            if data["createdBy"] != user.id:
                raise HTTPException(status_code=403, detail="Unauthorized")

        # Normalize createdAt
        if "createdAt" in data:
            if hasattr(data["createdAt"], "to_datetime"):
                data["createdAt"] = data["createdAt"].to_datetime()
            elif isinstance(data["createdAt"], str):
                data["createdAt"] = datetime.fromisoformat(data["createdAt"])

        return Game(**data)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print("❌ Error in get_game_by_id:", e)
        raise HTTPException(status_code=500, detail="Internal server error")
