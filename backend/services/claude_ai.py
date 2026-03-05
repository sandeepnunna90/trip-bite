import json
import re
import anthropic
from backend.config import get_settings
from backend.models import Dish

MOCK_DISHES = [
    Dish(dish_name="Brisket", reason="Mentioned by nearly every reviewer as the must-order item. Perfectly smoked with a beautiful bark and juicy interior.", is_vegetarian=False, confidence="high"),
    Dish(dish_name="Pulled Pork Sandwich", reason="Praised for generous portions and flavorful sauce. A crowd favorite for first-time visitors.", is_vegetarian=False, confidence="high"),
    Dish(dish_name="Mac and Cheese", reason="Described as creamy and rich. Multiple reviewers call it the best side dish on the menu.", is_vegetarian=True, confidence="high"),
    Dish(dish_name="Ribs", reason="Full racks praised for perfect smoke and tender meat. The bark gets frequent compliments.", is_vegetarian=False, confidence="high"),
    Dish(dish_name="Banana Pudding", reason="Consistently mentioned as the perfect dessert ending. Light and creamy.", is_vegetarian=True, confidence="medium"),
    Dish(dish_name="Smoked Wings", reason="Called a hidden gem by several regulars. Crispy skin with deep smoky flavor.", is_vegetarian=False, confidence="medium"),
    Dish(dish_name="Jalapeño Cheddar Sausage", reason="Single mention but with high enthusiasm — spicy and flavorful.", is_vegetarian=False, confidence="low"),
]

EXTRACT_PROMPT = """You are a food intelligence assistant. Analyze the following restaurant reviews and extract the top 5-10 most frequently mentioned and praised dishes.

Return ONLY a valid JSON array. No explanation, no markdown, no preamble.

Each object must have:
- "dish_name": string
- "reason": string (1-2 sentences)
- "is_vegetarian": boolean
- "confidence": "high" | "medium" | "low"
  - high = mentioned 5+ times with enthusiasm
  - medium = mentioned 2-4 times
  - low = single mention or ambiguous

Reviews:
{reviews_text}"""

REPAIR_PROMPT = """The following text should be a JSON array of dish objects but may be malformed. Fix it and return ONLY valid JSON.

Each object must have: dish_name (string), reason (string), is_vegetarian (boolean), confidence ("high"|"medium"|"low").

Text to fix:
{broken_json}"""


def _strip_markdown(text: str) -> str:
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())
    return text.strip()


def _parse_dishes(raw: str) -> list[Dish]:
    cleaned = _strip_markdown(raw)
    data = json.loads(cleaned)
    return [Dish(**item) for item in data]


def extract_dishes(reviews: list[str]) -> list[Dish]:
    settings = get_settings()

    if settings.use_mock_claude:
        return MOCK_DISHES

    reviews_text = "\n\n".join(f"Review {i+1}: {r}" for i, r in enumerate(reviews))
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": EXTRACT_PROMPT.format(reviews_text=reviews_text),
            }
        ],
    )
    raw = message.content[0].text

    try:
        return _parse_dishes(raw)
    except (json.JSONDecodeError, Exception):
        # Retry with repair prompt
        repair_message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": REPAIR_PROMPT.format(broken_json=raw),
                }
            ],
        )
        return _parse_dishes(repair_message.content[0].text)
