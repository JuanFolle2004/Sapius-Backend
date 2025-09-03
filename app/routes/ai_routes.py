from fastapi import APIRouter, Depends, HTTPException, Body
from app.models.user_model import User
from app.utils.auth import get_current_user
from app.firebase.firebase_config import db
from uuid import uuid4
from google.cloud import firestore
from dotenv import load_dotenv
import os
from datetime import datetime

from app.services.generation import generate_games_from_prompt
from app.services.normalization import normalize_topic
from app.models.game import Game

# Load .env and OpenAI key
load_dotenv()
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter(prefix="/ai", tags=["AI"])

# -------------------------------
# Duration → Question count mapping
# -------------------------------
DURATION_TO_COUNT = {5: 3, 10: 6, 15: 8}

def questions_from_duration(duration: int) -> int:
    if duration not in DURATION_TO_COUNT:
        raise HTTPException(
            status_code=400,
            detail="Duration must be 5, 10, or 15 minutes."
        )
    return DURATION_TO_COUNT[duration]

# -------------------------------
# Generate games for an existing folder
# -------------------------------
@router.post("/generate-from-folder/{folder_id}", response_model=list[Game])
def generate_from_existing_folder(
    folder_id: str,
    duration: int = Body(5, embed=True),
    difficulty: str = Body("same", embed=True),  # 👈 new parameter
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

    # 🔹 Adjust prompt depending on difficulty
    if difficulty == "easier":
        prompt += " (make the questions easier, suitable for beginners)"
    elif difficulty == "harder":
        prompt += " (make the questions more challenging, advanced vocabulary and harder questions)"
    # "same" → no change

    try:
        raw_games = generate_games_from_prompt(prompt, count=num_questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT call failed: {str(e)}")

    saved_games = []
    for i, g in enumerate(raw_games):
        q = g.get("question")
        options = g.get("options", [])
        correct = g.get("correctAnswer")
        explanation = g.get("explanation")
        topic = g.get("topic", prompt)

        if not q or not isinstance(options, list) or len(options) != 4:
            print("⚠️ Skipping invalid game:", g)
            continue
        if correct not in options:
            print("⚠️ Correct answer not in options, fixing:", correct)
            correct = options[0]

        game_id = str(uuid4())
        created_at = datetime.utcnow()

        main_topic = normalize_topic(topic, fallback=prompt)
        tags = [topic] if topic else []

        game_data = {
            "id": game_id,
            "order": i + 1,
            "title": q[:30],
            "question": q,
            "options": options,
            "correctAnswer": correct,
            "explanation": explanation or "",
            "createdAt": created_at,
            "createdBy": user.id,
            "folderId": folder_id,
            "topic": main_topic,
            "tags": tags,
            "difficulty": difficulty,  # 👈 store difficulty info
        }

        db.collection("games").document(game_id).set(game_data)
        db.collection("folders").document(folder_id).update({
            "gameIds": firestore.ArrayUnion([game_id])
        })

        saved_games.append(game_data)

    return saved_games
