from fastapi import APIRouter, Depends, HTTPException
from app.firebase.firebase_config import db
from app.models.folder import Folder
from app.models.game import Game
from app.models.user_model import User
from app.utils.auth import get_current_user
from typing import List, Dict

router = APIRouter(prefix="/folders", tags=["Folders"])

@router.get("/{folder_id}/with-games")
def get_folder_with_games(folder_id: str, current_user: dict = Depends(get_current_user)):
    folder_doc = db.collection("folders").document(folder_id).get()
    if not folder_doc.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_data = folder_doc.to_dict()

    # Get full game objects
    game_ids = folder_data.get("gameIds", [])
    games = []
    for gid in game_ids:
        game_doc = db.collection("games").document(gid).get()
        if game_doc.exists:
            game = game_doc.to_dict()
            game["id"] = game_doc.id  # ensure ID is included
            games.append(game)

    return {
        "folder": folder_data,
        "games": games
    }
