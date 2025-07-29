from fastapi import APIRouter, Depends, HTTPException
from app.firebase.firebase_config import db
from app.models.game import Game
from app.models.user_model import User
from app.utils.auth import get_current_user
from uuid import uuid4
from datetime import datetime
from typing import List
from pydantic import BaseModel
from google.cloud import firestore
from google.cloud.firestore_v1 import DocumentSnapshot

router = APIRouter(prefix="/games", tags=["Games"])


# Request body for creating a game
class GameCreate(BaseModel):
    order: int
    question: str
    options: List[str]
    correctAnswer: str
    explanation: str
    folderId: str
    title: str


@router.post("/", response_model=Game)
def create_game(game: GameCreate, current_user: User = Depends(get_current_user)):
    # Verify that the folder exists
    folder_ref = db.collection("folders").document(game.folderId).get()
    if not folder_ref.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    # Generate game ID and prepare game data
    game_id = str(uuid4())
    game_data = {
        "id": game_id,
        "order": game.order,
        "question": game.question,
        "options": game.options,
        "correctAnswer": game.correctAnswer,
        "explanation": game.explanation,
        "createdBy": current_user.id,
        "createdAt": datetime.utcnow(),  # use datetime directly
        "folderId": game.folderId,
        "title": game.title,
    }

    # Save the game first
    db.collection("games").document(game_id).set(game_data)

    # Then update the folder to include this game's ID
    db.collection("folders").document(game.folderId).update({
        "gameIds": firestore.ArrayUnion([game_id])
    })

    return Game(**game_data)


@router.get("/", response_model=List[Game])
def list_games(current_user: User = Depends(get_current_user)):
    query = db.collection("games").where("createdBy", "==", current_user.id).stream()
    return [Game(**doc.to_dict()) for doc in query]



@router.get("/folder/{folder_id}", response_model=List[Game])
def get_games_by_folder(folder_id: str, current_user: User = Depends(get_current_user)):
    folder_ref = db.collection("folders").document(folder_id).get()
    if not folder_ref.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_data = folder_ref.to_dict()
    if folder_data["createdBy"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this folder's games")

    query = db.collection("games").where("folderId", "==", folder_id).where("createdBy", "==", current_user.id).stream()
    games = []
    for doc in query:
        data = doc.to_dict()
        data["docId"] = doc.id
        games.append(data)
    return games


@router.get("/{game_id}", response_model=Game)
def get_game_by_id(game_id: str, user: User = Depends(get_current_user)):
    try:
        doc = db.collection("games").document(game_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Game not found")

        data = doc.to_dict()
        print("🔥 Raw game data from Firestore:", data)

        print("🔐 Requesting user ID:", user.id)
        print("🆔 Game createdBy ID:", data["createdBy"])

        if data["createdBy"] != user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        data["id"] = doc.id

        if "createdAt" in data:
            if hasattr(data["createdAt"], "to_datetime"):
                data["createdAt"] = data["createdAt"].to_datetime()
            elif isinstance(data["createdAt"], str):
                from datetime import datetime
                data["createdAt"] = datetime.fromisoformat(data["createdAt"])

        return Game(**data)

    except HTTPException as http_exc:
        raise http_exc  # ✅ preserve 403/404
    except Exception as e:
        print("❌ Error in get_game_by_id:", e)
        raise HTTPException(status_code=500, detail="Internal server error")








