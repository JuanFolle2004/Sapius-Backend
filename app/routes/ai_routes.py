from fastapi import APIRouter, Depends, HTTPException, Body
from app.models.user_model import User
from app.utils.auth import get_current_user
from app.firebase.firebase_config import db
from google.cloud import firestore
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
import os
import json
import random

from app.services.generation import generate_games_from_prompt
from app.services.normalization import normalize_topic
from app.models.game import Game

# Load .env and OpenAI key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter(prefix="/ai", tags=["AI"])

# -------------------------------
# Duration → Question count mapping
# -------------------------------
DURATION_TO_COUNT = {
    5: 3,
    10: 6,
    15: 8
}

def questions_from_duration(duration: int) -> int:
    if duration not in DURATION_TO_COUNT:
        raise HTTPException(
            status_code=400,
            detail="Duration must be 5, 10, or 15 minutes."
        )
    return DURATION_TO_COUNT[duration]

# -------------------------------
# Request model for game generation
# -------------------------------
class GenerationRequest(BaseModel):
    prompt: str
    folderId: str
    duration: int   # must be 5, 10, or 15

# -------------------------------
# Generate new games from prompt
# -------------------------------
def generate_games(
    data: GenerationRequest,
    current_user: User = Depends(get_current_user)
):
    num_questions = questions_from_duration(data.duration)

    system_prompt = (
        f"You are a quiz generator. Given a topic, generate {num_questions} quiz games in JSON format. "
        "Each game must include:\n"
        "- question: string\n"
        "- options: array of 4 strings\n"
        "- correctAnswer: one of the options\n"
        "- explanation: string\n"
        "- topic: string (e.g. 'history', 'math', 'geography')\n\n"
        "Respond only with a JSON array of objects."
    )

    user_prompt = f"Topic: {data.prompt}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        raw = response.choices[0].message.content.strip()
        try:
            games = json.loads(raw)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail="AI response could not be parsed as JSON."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")

    saved_games = []
    for i, game in enumerate(games):
        game_id = str(uuid4())

        # normalize + tags
        main_topic = normalize_topic(game.get("topic"), fallback=data.prompt)
        raw_tag = game.get("topic") or data.prompt
        tags = [raw_tag] if raw_tag else []

        game_data = {
            "id": game_id,
            "folderId": data.folderId,
            "createdBy": current_user.id,
            "createdAt": datetime.utcnow().isoformat(),
            "order": i + 1,
            "question": game["question"],
            "options": game["options"],
            "correctAnswer": game["correctAnswer"],
            "explanation": game["explanation"],
            "title": game["question"][:30],
            "topic": main_topic,
            "tags": tags
        }

        db.collection("games").document(game_id).set(game_data)
        db.collection("folders").document(data.folderId).update({
            "gameIds": firestore.ArrayUnion([game_id])
        })

        saved_games.append(game_data)

    return {"games": saved_games}

# -------------------------------
# Generate from existing folder
# -------------------------------
@router.post("/generate-from-folder/{folder_id}", response_model=list[Game])
def generate_from_existing_folder(
    folder_id: str,
    duration: int = Body(5, embed=True),  # default = 5 → 3 questions
    user: User = Depends(get_current_user)
):
    folder_ref = db.collection("folders").document(folder_id).get()
    if not folder_ref.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder = folder_ref.to_dict()
    if folder["createdBy"] != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    prompt = folder.get("prompt", "General knowledge")
    num_questions = questions_from_duration(duration)

    try:
        generated = generate_games_from_prompt(prompt, count=num_questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail="GPT call failed")

    saved_games = []
    for i, g in enumerate(generated):
        game_id = str(uuid4())

        main_topic = normalize_topic(g.get("topic"), fallback=prompt)
        raw_tag = g.get("topic") or prompt
        tags = [raw_tag] if raw_tag else []

        game_data = {
            "id": game_id,
            "order": i + 1,
            "title": g["question"][:30],
            "question": g["question"],
            "options": g["options"],
            "correctAnswer": g["correctAnswer"],
            "explanation": g["explanation"],
            "createdAt": datetime.utcnow().isoformat(),
            "createdBy": user.id,
            "folderId": folder_id,
            "topic": main_topic,
            "tags": tags
        }

        db.collection("games").document(game_id).set(game_data)
        db.collection("folders").document(folder_id).update({
            "gameIds": firestore.ArrayUnion([game_id])
        })

        saved_games.append(game_data)

    return saved_games
