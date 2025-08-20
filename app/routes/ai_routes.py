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
from app.services.generation import generate_games_from_prompt
from app.models.game import Game



# Load .env and OpenAI key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter(prefix="/ai", tags=["AI"])



# Define request format
class GenerationRequest(BaseModel):
    prompt: str
    folderId: str
    count: int = 3


@router.post("/generate-games")
def generate_games(data: GenerationRequest, current_user: User = Depends(get_current_user)):
    # Build the system prompt
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
            model="gpt-4",  # or "gpt-3.5-turbo" if cheaper
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )

        raw = response.choices[0].message.content.strip()

        # Safely parse the AI response
        try:
            games = json.loads(raw)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="AI response could not be parsed as JSON.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")

    # Save games to Firestore
    saved_games = []
    for i, game in enumerate(games):
        game_id = str(uuid4())
        game_data = {
            "id": game_id,
            "folderId": data.folderId,
            "createdBy": current_user.id,
            "createdAt": datetime.utcnow(),
            "order": i + 1,
            "question": game["question"],
            "options": game["options"],
            "correctAnswer": game["correctAnswer"],
            "explanation": game["explanation"],
            "title": game["question"][:30],
            "topic": game.get("topic", data.prompt)
        }

        # Save to games collection
        db.collection("games").document(game_id).set(game_data)

        # Update folder
        db.collection("folders").document(data.folderId).update({
            "gameIds": firestore.ArrayUnion([game_id])
        })

        saved_games.append(game_data)

    return {"games": saved_games}
@router.post("/generate-from-folder/{folder_id}", response_model=list[Game])
def generate_from_existing_folder(folder_id: str, user: User = Depends(get_current_user)):
    print("📥 Request received for folder:", folder_id)

    folder_ref = db.collection("folders").document(folder_id).get()
    if not folder_ref.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder = folder_ref.to_dict()
    if folder["createdBy"] != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    print("✅ Folder found:", folder)

    prompt = folder.get("prompt", "General knowledge")
    print("📡 Calling GPT with prompt:", prompt)

    try:
        generated = generate_games_from_prompt(prompt)
    except Exception as e:
        print("🔥 GPT call failed:", e)
        raise HTTPException(status_code=500, detail="GPT call failed")

    print("✅ Games generated:", generated)

    saved_games = []
    for i, g in enumerate(generated):
        game_id = str(uuid4())
        game_data = {
            "id": game_id,
            "order": i + 1,
            "title": g["question"][:30],
            "question": g["question"],
            "options": g["options"],
            "correctAnswer": g["correctAnswer"],
            "explanation": g["explanation"],
            "createdAt": datetime.utcnow(),
            "createdBy": user.id,
            "folderId": folder_id,
            "topic": g.get("topic", prompt)
        }

        # Save to Firestore
        db.collection("games").document(game_id).set(game_data)

        # Update folder with new game ID
        db.collection("folders").document(folder_id).update({
            "gameIds": firestore.ArrayUnion([game_id])
        })

        saved_games.append(game_data)

    return saved_games





