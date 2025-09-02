import os
import json
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_games_from_prompt(prompt: str, count: int = 3):
    """
    Ask GPT to generate quiz games.
    Returns a list of dicts with raw fields from GPT (no ids, no metadata).
    """

    system_prompt = (
        f"You are a quiz generator. Given a topic, generate {count} quiz games in JSON format. "
        "Each game must include:\n"
        "- question: string\n"
        "- options: array of 4 strings\n"
        "- correctAnswer: one of the options\n"
        "- explanation: string\n"
        "- topic: string (e.g. 'history', 'math', 'geography')\n\n"
        "Respond only with a JSON array of objects."
    )

    user_prompt = f"Topic: {prompt}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        raw = response.choices[0].message["content"].strip()
        print("🔎 RAW GPT OUTPUT (first 500 chars):", raw[:500])

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
