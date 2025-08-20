from fastapi import APIRouter, Depends, HTTPException
from app.firebase.firebase_config import db
from app.models.folder import Folder, FolderCreate
from app.models.user_model import User
from app.utils.auth import get_current_user
from typing import List
from datetime import datetime
from uuid import uuid4
import random

router = APIRouter(prefix="/folders", tags=["Folders"])

# POST /folders – Create a folder
@router.post("/", response_model=Folder)
def create_folder(folder: FolderCreate, current_user: User = Depends(get_current_user)):
    folder_id = str(uuid4())
    folder_data = {
        "id": folder_id,
        "title": folder.title,
        "description": folder.description,
        "prompt": folder.prompt,
        "createdBy": current_user.id,
        "createdAt": datetime.utcnow(),
        "gameIds": []
    }

    db.collection("folders").document(folder_id).set(folder_data)
    return Folder(**folder_data)

# GET /folders – List folders for current user
@router.get("/", response_model=List[Folder])
def list_folders(current_user: User = Depends(get_current_user)):
    user_id = current_user.id
    folders_ref = db.collection("folders").where("createdBy", "==", user_id).stream()
    folders = []
    for doc in folders_ref:
        folder_data = doc.to_dict()
        folder_data["id"] = doc.id
        folders.append(Folder(**folder_data))
    return folders

# GET /folders/{folder_id}/with-games – Folder + its games
@router.get("/{folder_id}/with-games")
def get_folder_with_games(folder_id: str, current_user: User = Depends(get_current_user)):
    folder_doc = db.collection("folders").document(folder_id).get()
    if not folder_doc.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_data = folder_doc.to_dict()
    folder_data["id"] = folder_id

    if folder_data["createdBy"] != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    game_docs = db.collection("games")\
        .where("folderId", "==", folder_id)\
        .where("createdBy", "==", current_user.id)\
        .stream()

    games = []
    for doc in game_docs:
        game = doc.to_dict()
        game["id"] = doc.id
        games.append(game)

    return {
        "folder": folder_data,
        "games": games
    }

# GET /folders/{folder_id} – Folder basic info only
@router.get("/{folder_id}", response_model=Folder)
def get_folder_details(folder_id: str, current_user: User = Depends(get_current_user)):
    folder_doc = db.collection("folders").document(folder_id).get()
    if not folder_doc.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_data = folder_doc.to_dict()
    folder_data["id"] = folder_id

    if folder_data["createdBy"] != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return Folder(**folder_data)

# 🎲 GET /folders/random/with-games – Random folder with user-interest games
@router.get("/random/with-games")
def get_random_folder_with_games(current_user: User = Depends(get_current_user)):
    if not current_user.interests or len(current_user.interests) == 0:
        raise HTTPException(status_code=400, detail="User has no interests defined")

    all_interest_games = []

    # 🔎 fetch games for each interest
    for interest in current_user.interests:
        game_docs = db.collection("games")\
            .where("topic", "==", interest)\
            .limit(50)\
            .stream()
        for doc in game_docs:
            game = doc.to_dict()
            game["id"] = doc.id
            all_interest_games.append(game)

    if not all_interest_games:
        raise HTTPException(status_code=404, detail="No games found for user interests")

    # 🎲 Pick up to 10 random games
    selected_games = random.sample(all_interest_games, min(10, len(all_interest_games)))

    folder_data = {
        "id": "random",
        "title": "🎲 Random Quiz",
        "description": "Random questions from your topics of interest",
        "prompt": None,
        "createdBy": "system",
        "createdAt": datetime.utcnow(),
        "gameIds": [g["id"] for g in selected_games],
    }

    return {
        "folder": folder_data,
        "games": selected_games
    }