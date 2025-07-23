import os
from dotenv import load_dotenv

# ✅ Load .env from Back/.env (2 levels up from generation.py)
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path=env_path)

from openai import OpenAI
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

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )

    content = response.choices[0].message.content.strip()

    print("🧠 Raw AI response:", content)  # 👈 Log what GPT sends back

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("❌ Failed to decode AI response:", content)
        return []
