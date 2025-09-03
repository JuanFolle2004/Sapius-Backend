import os
import json
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_games_from_prompt(prompt: str, count: int = 3):
    """
    Generate quiz games from a topic using OpenAI.
    Ensures: valid topic, appropriate content, confident response.
    Returns a list of dicts (question, options, correctAnswer, explanation, topic).
    """

    system_prompt = (
        "You are a quiz generator. "
        "If the topic is inappropriate (violence, hate, sex, politics, etc.) "
        "or if you are not confident you understand it, respond with: {\"status\":\"UNSUITABLE\"}. "
        f"Otherwise, generate {count} quiz games in a pure JSON array. "
        "Each object must have exactly:\n"
        "question (string),\n"
        "options (array of 4 strings),\n"
        "correctAnswer (one of the options),\n"
        "explanation (string),\n"
        "topic (string like 'history','math','geography')."
    )

    user_prompt = f"Topic: {prompt}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,   # lower = more reliable JSON
        )

        raw = response.choices[0].message["content"].strip()
        print("🔎 RAW GPT OUTPUT (first 300 chars):", raw[:300])

        # Handle refusal
        if raw.startswith("{") and "\"status\":\"UNSUITABLE\"" in raw:
            raise ValueError("❌ Topic unsuitable or AI not confident.")

        # Clean code fences
        if "```" in raw:
            raw = raw.split("```")
            raw = next((part for part in raw if "{" in part or "[" in part), "").strip()
            raw = raw.replace("json", "").strip()

        games_json = json.loads(raw)

        if not isinstance(games_json, list):
            raise ValueError("Expected a JSON array of games")

        return games_json

    except Exception as e:
        print("❌ GPT generation error:", str(e))
        raise RuntimeError(f"OpenAI error: {str(e)}")
