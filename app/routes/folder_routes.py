from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4
from datetime import datetime
from app.firebase.firebase_config import db
from app.models.folder import Folder
from app.models.user_model import User
from app.utils.auth import get_current_user
from pydantic import BaseModel
from typing import Optional

# only import the generate function, not the request schema
from app.routes.ai_routes import generate_games

router = APIRouter(prefix="/folders", tags=["Folders"])


# -------------------------------
# Request model ONLY for creating new folders with games
# -------------------------------
class FolderWithGamesRequest(BaseModel):
    prompt: str
    duration: int  # must be 5, 10, or 15
    title: Optional[str] = None
    description: Optional[str] = None


# -------------------------------
# Create folder + generate games
# -------------------------------
@router.post("/with-games")
def create_folder_with_games(
    data: FolderWithGamesRequest,
    current_user: User = Depends(get_current_user)
):
    folder_id = str(uuid4())
    created_at = datetime.utcnow().isoformat()

    folder_data = {
        "id": folder_id,
        "title": data.title or data.prompt,
        "description": data.description or f"AI-generated course on {data.prompt}",
        "prompt": data.prompt,
        "createdBy": current_user.id,
        "createdAt": created_at,
        "gameIds": []
    }

    db.collection("folders").document(folder_id).set(folder_data)

    # ✅ Import the correct request model here, not at the top
    from app.routes.ai_routes import GenerationRequest
    result = generate_games(
        GenerationRequest(prompt=data.prompt, folderId=folder_id, duration=data.duration),
        current_user
    )

    return {"folder": folder_data, "games": result["games"]}
