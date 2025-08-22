from difflib import get_close_matches
from app.constants.interests import STANDARD_INTERESTS

SYNONYMS = {
    "cinema": "movies",
    "film": "movies",
    "football": "sports",
    "soccer": "sports",
    "basketball": "sports",
    "painting": "art",
    "drawing": "art",
    "programming": "technology",
    "coding": "technology",
    "ai": "technology",
    "machine learning": "technology",
}

def normalize_topic(gpt_topic: str, fallback: str = "general") -> str:
    """
    Normalize GPT topic into one of the STANDARD_INTERESTS.
    Uses synonyms first, then fuzzy match, otherwise fallback.
    """
    if not gpt_topic:
        return fallback

    gpt_topic = gpt_topic.lower().strip()

    # 1. Synonym direct mapping
    if gpt_topic in SYNONYMS:
        return SYNONYMS[gpt_topic]

    # 2. Fuzzy match against the 20 categories
    matches = get_close_matches(gpt_topic, STANDARD_INTERESTS, n=1, cutoff=0.4)
    return matches[0] if matches else fallback
