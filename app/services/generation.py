import os
import json
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_games_from_prompt(prompt: str, count: int = 3):
    """
    Generate quiz games using OpenAI GPT.
    Returns a list of game objects parsed from JSON.
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
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        raw = response.choices[0].message["content"].strip()

        try:
            games = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError("OpenAI response could not be parsed as JSON.")

        return games

    except Exception as e:
        raise RuntimeError(f"OpenAI error: {str(e)}")
