import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

# Load .env manually (adjust path as needed)
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path=env_path)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_games_from_prompt(prompt: str, count: int = 3):
    system_prompt = (
        f"You are a quiz generator. Given a topic, generate {count} quiz games in JSON format. "
        "Each game must include:\n"
        "- question: string\n"
        "- options: array of 4 strings\n"
        "- correctAnswer: one of the options\n"
        "- explanation: string\n\n"
        "Respond only with a JSON array of objects."
    )

    user_prompt = f"Topic: {prompt}"

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
        )
    except Exception as e:
        print("❌ OpenAI API error:", e)
        raise

    content = response.choices[0].message.content.strip()
    print("🤖 Raw GPT response:", content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("❌ Failed to decode GPT response.")
        return []
