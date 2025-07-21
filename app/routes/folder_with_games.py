from fastapi import APIRouter, Depends, HTTPException
from app.firebase.firebase_config import db
from app.models.folder import Folder
from app.models.game import Game
from app.models.user_model import User
from app.utils.auth import get_current_user
from typing import List, Dict

router = APIRouter(prefix="/folders", tags=["Folders"])

@router.get("/{folder_id}/with-games")
def get_folder_with_games(folder_id: str, current_user: User = Depends(get_current_user)):
    folder_doc = db.collection("folders").document(folder_id).get()

    if not folder_doc.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_data = folder_doc.to_dict()

    if folder_data["createdBy"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this folder")

    # Fetch games based on stored gameIds
    game_ids = folder_data.get("gameIds", [])
    games = []

    for gid in game_ids:
        game_doc = db.collection("games").document(gid).get()
        if game_doc.exists:
            games.append(game_doc.to_dict())

    return {
        "folder": folder_data,
        "games": games
    }
