import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

import re
from typing import List, Dict

# Load .env manually (adjust path as needed)
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path=env_path)

print("🔐 OPENAI KEY LOADED:", os.getenv("OPENAI_API_KEY"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_games_from_prompt(prompt: str, count: int = 3):
    system_prompt = (
        f"You are a helpful assistant that generates educational quiz questions based on a topic.\n"
        f"Generate {count} multiple choice questions (MCQ) about: {prompt}.\n"
        f"Each question must have 4 options, one correct answer, and a short explanation.\n"
        f"Respond in valid JSON list format, like:\n"
        f"[{{'question': '...', 'options': ['A', 'B', 'C', 'D'], 'correctAnswer': '...', 'explanation': '...'}}, ...]"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please generate the questions now."}
        ],
        temperature=0.9,
        max_tokens=1000,
    )

    raw_text = response.choices[0].message.content
    print("📡 GPT raw response:", raw_text)

    return parse_questions_from_text(raw_text)  # Make sure this function handles stringified JSON


def parse_questions_from_text(text: str) -> List[Dict]:
    """
    Parse a GPT-generated JSON string or pseudo-JSON list of games.
    Expected structure:
    [
        {
            "question": "...",
            "options": ["A", "B", "C", "D"],
            "correctAnswer": "...",
            "explanation": "..."
        },
        ...
    ]
    """
    try:
        # Try parsing as is
        return json.loads(text)
    except json.JSONDecodeError:
        print("⚠️ Initial parse failed — trying to sanitize JSON...")

        # Attempt to fix common JSON formatting issues
        # Replace single quotes with double quotes
        sanitized = text.replace("‘", '"').replace("’", '"').replace("“", '"').replace("”", '"')
        sanitized = re.sub(r"(?<!\\)\'", '"', sanitized)

        # Ensure keys have quotes
        sanitized = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1 "\2":', sanitized)

        # Remove trailing commas (which are invalid in JSON)
        sanitized = re.sub(r",\s*}", "}", sanitized)
        sanitized = re.sub(r",\s*]", "]", sanitized)

        try:
            return json.loads(sanitized)
        except Exception as e:
            print("❌ Could not parse GPT output:", e)
            print("🔴 Raw sanitized text:\n", sanitized)
            raise ValueError("Failed to parse GPT-generated questions.")

