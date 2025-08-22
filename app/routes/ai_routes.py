from fastapi import APIRouter, Depends, HTTPException
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


class GenerationRequest(BaseModel):
    prompt: str
    folderId: str
    count: int = 3


# -------------------------------
# Generate new games from prompt
# -------------------------------
def generate_games(data: GenerationRequest, current_user: User = Depends(get_current_user)):
    system_prompt = (
        f"You are a quiz generator. Given a topic, generate {data.count} quiz games in JSON format. "
        "Each game must include:\n"
        "- question: string\n"
        "- options: array of 4 strings\n"
        "- correctAnswer: one of the options\n"
        "- explanation: string\n"
        "- topic: string (the category of the question, e.g. 'history', 'math', 'geography')\n\n"
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
            raise HTTPException(status_code=500, detail="AI response could not be parsed as JSON.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")

    saved_games = []
    for i, game in enumerate(games):
        game_id = str(uuid4())

        # ✅ normalize + tags
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
def generate_from_existing_folder(folder_id: str, user: User = Depends(get_current_user)):
    folder_ref = db.collection("folders").document(folder_id).get()
    if not folder_ref.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder = folder_ref.to_dict()
    if folder["createdBy"] != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    prompt = folder.get("prompt", "General knowledge")
    try:
        generated = generate_games_from_prompt(prompt)
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


# -------------------------------
# Random folder with games
# -------------------------------
@router.get("/folders/random/with-games")
def get_random_folder_with_games(current_user: User = Depends(get_current_user)):
    if not current_user.interests or len(current_user.interests) == 0:
        raise HTTPException(status_code=400, detail="User has no interests defined")

    all_interest_games = []

    for interest in current_user.interests:
        game_docs = (
            db.collection("games")
            .where("topic", "==", interest)
            .limit(50)
            .stream()
        )
        for doc in game_docs:
            game = doc.to_dict()
            game["id"] = doc.id
            all_interest_games.append(game)

    if not all_interest_games:
        chosen_interest = random.choice(current_user.interests)
        # fallback: generate 2 games
        from app.services.generation import generate_games_from_prompt
        generated = generate_games_from_prompt(chosen_interest)

        for i, g in enumerate(generated):
            game_id = str(uuid4())
            main_topic = normalize_topic(g.get("topic"), fallback=chosen_interest)
            raw_tag = g.get("topic") or chosen_interest
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
                "createdBy": current_user.id,
                "folderId": None,  # virtual folder
                "topic": main_topic,
                "tags": tags
            }
            db.collection("games").document(game_id).set(game_data)
            all_interest_games.append(game_data)

    selected_games = random.sample(all_interest_games, min(10, len(all_interest_games)))

    folder_data = {
        "id": "random",
        "title": "🎲 Random Quiz",
        "description": "Random questions from your topics of interest",
        "prompt": None,
        "createdBy": "system",
        "createdAt": datetime.utcnow().isoformat(),
        "gameIds": [g["id"] for g in selected_games],
    }

    return {"folder": folder_data, "games": selected_games}
