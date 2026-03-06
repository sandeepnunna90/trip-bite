from apify_client import ApifyClient
from backend.config import get_settings

ACTOR_ID = "compass/google-maps-reviews-scraper"

MOCK_REVIEWS = [
    "The brisket here is absolutely incredible - smoky, tender, falls apart. Best BBQ I've had!",
    "Must try the pulled pork sandwich. They pile it high and the sauce is perfect.",
    "Ribs were outstanding! Perfectly smoked with a beautiful bark. Got the full rack.",
    "The mac and cheese side is criminally underrated. Creamy, rich, amazing.",
    "Brisket brisket brisket. That's all you need to know. Get the brisket.",
    "Pulled pork was incredible, but honestly the cornbread stole the show for me.",
    "Smoked wings are a hidden gem here. Crispy skin, smoky flavor throughout.",
    "The coleslaw is fresh and tangy - great counterpoint to the rich meats.",
    "Brisket sandwich is massive and worth every penny. Smoke ring was gorgeous.",
    "Tried the veggie plate - black eyed peas and collard greens were delicious!",
    "Banana pudding for dessert is a must. Don't leave without ordering it.",
    "The burnt ends were on special and they were phenomenal. Get them if available.",
    "Pulled pork nachos - sounds weird, tastes amazing. Trust me on this one.",
    "Best smoked turkey I've ever had. Moist, flavorful, not dry at all.",
    "The potato salad is homemade and delicious. Perfect side for the ribs.",
    "Brisket brisket brisket - juicy, perfect smoke, incredible bark.",
    "Half chicken was tender and smoky. Great for someone who wants lighter option.",
    "Mac and cheese is top tier. Could eat a whole bowl as a meal.",
    "The jalapeño cheddar sausage links were spicy and delicious.",
    "Banana pudding was the highlight of my meal. Light, creamy, perfect end.",
]


def get_reviews(place_id: str) -> list[str]:
    settings = get_settings()

    if settings.use_mock_apify:
        return MOCK_REVIEWS

    client = ApifyClient(settings.apify_api_token)

    run_input = {
        "placeIds": [f"https://www.google.com/maps/place/?q=place_id:{place_id}"],
        "maxReviews": settings.apify_max_reviews,
        "reviewsSort": "mostRelevant",
        "language": "en",
    }

    run = client.actor(ACTOR_ID).call(run_input=run_input, timeout_secs=150)

    reviews = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        text = item.get("text") or item.get("reviewText") or item.get("snippet", "")
        if text:
            reviews.append(text.strip())

    return reviews
