import httpx
from datetime import datetime, timedelta, timezone
from backend.config import get_settings
from backend.models import RestaurantCard
from backend.services.supabase_client import get_service_client

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
CACHE_TTL_HOURS = 24

MOCK_RESTAURANTS = [
    RestaurantCard(
        place_id="mock_bbq_1",
        name="Peg Leg Porker",
        rating=4.7,
        review_count=3200,
        price_level="$$",
        address="903 Gleaves St, Nashville, TN 37203",
        photo_url="https://placehold.co/400x300?text=Peg+Leg+Porker",
        lat=36.1545,
        lng=-86.7812,
    ),
    RestaurantCard(
        place_id="mock_bbq_2",
        name="Martin's Bar-B-Que Joint",
        rating=4.6,
        review_count=4100,
        price_level="$$",
        address="410 4th Ave S, Nashville, TN 37201",
        photo_url="https://placehold.co/400x300?text=Martins+BBQ",
        lat=36.1562,
        lng=-86.7760,
    ),
    RestaurantCard(
        place_id="mock_bbq_3",
        name="Edley's Bar-B-Que",
        rating=4.5,
        review_count=2800,
        price_level="$$",
        address="2706 12th Ave S, Nashville, TN 37204",
        photo_url="https://placehold.co/400x300?text=Edleys+BBQ",
        lat=36.1281,
        lng=-86.7942,
    ),
    RestaurantCard(
        place_id="mock_bbq_4",
        name="Hattie B's Hot Chicken",
        rating=4.6,
        review_count=5600,
        price_level="$$",
        address="112 19th Ave S, Nashville, TN 37203",
        photo_url="https://placehold.co/400x300?text=Hattie+Bs",
        lat=36.1504,
        lng=-86.7986,
    ),
    RestaurantCard(
        place_id="mock_bbq_5",
        name="Shotgun Willie's BBQ",
        rating=4.5,
        review_count=1200,
        price_level="$",
        address="215 Louise Ave, Nashville, TN 37203",
        photo_url="https://placehold.co/400x300?text=Shotgun+Willies",
        lat=36.1490,
        lng=-86.7840,
    ),
]


def _price_level_symbol(level: int | None) -> str | None:
    if level is None:
        return None
    mapping = {1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}
    return mapping.get(level)


def _build_photo_url(photo_name: str, api_key: str) -> str:
    return f"https://places.googleapis.com/v1/{photo_name}/media?maxWidthPx=400&key={api_key}"


def _cache_restaurants(restaurants: list[RestaurantCard]) -> None:
    client = get_service_client()
    rows = [
        {
            "place_id": r.place_id,
            "name": r.name,
            "rating": r.rating,
            "review_count": r.review_count,
            "price_level": r.price_level,
            "address": r.address,
            "photo_url": r.photo_url,
            "lat": r.lat,
            "lng": r.lng,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        for r in restaurants
    ]
    client.table("restaurant_cache").upsert(rows).execute()


def search_restaurants(city: str, cuisine: str) -> list[RestaurantCard]:
    settings = get_settings()

    if settings.use_mock_google:
        return MOCK_RESTAURANTS

    query = f"{cuisine} restaurants in {city}" if cuisine.lower() != "any" else f"best restaurants in {city}"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.google_places_api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.rating,places.userRatingCount,"
            "places.priceLevel,places.formattedAddress,places.photos,"
            "places.location"
        ),
    }
    payload = {"textQuery": query, "maxResultCount": 20, "languageCode": "en"}

    with httpx.Client(timeout=15) as client:
        resp = client.post(PLACES_SEARCH_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    results: list[RestaurantCard] = []
    for place in data.get("places", []):
        rating = place.get("rating", 0)
        review_count = place.get("userRatingCount", 0)
        if rating < 4.5 or review_count < 1000:
            continue

        photos = place.get("photos", [])
        photo_url = (
            _build_photo_url(photos[0]["name"], settings.google_places_api_key)
            if photos
            else None
        )

        location = place.get("location", {})
        price_raw = place.get("priceLevel")
        price_map = {
            "PRICE_LEVEL_FREE": "$",
            "PRICE_LEVEL_INEXPENSIVE": "$",
            "PRICE_LEVEL_MODERATE": "$$",
            "PRICE_LEVEL_EXPENSIVE": "$$$",
            "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$",
        }

        results.append(
            RestaurantCard(
                place_id=place["id"],
                name=place["displayName"]["text"],
                rating=rating,
                review_count=review_count,
                price_level=price_map.get(price_raw) if price_raw else None,
                address=place.get("formattedAddress", ""),
                photo_url=photo_url,
                lat=location.get("latitude"),
                lng=location.get("longitude"),
            )
        )

    _cache_restaurants(results)
    return results


def get_restaurant(place_id: str) -> RestaurantCard | None:
    settings = get_settings()

    if settings.use_mock_google:
        for r in MOCK_RESTAURANTS:
            if r.place_id == place_id:
                return r
        return None

    # Check cache first
    client = get_service_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS)).isoformat()
    row = (
        client.table("restaurant_cache")
        .select("*")
        .eq("place_id", place_id)
        .gte("cached_at", cutoff)
        .maybe_single()
        .execute()
    )
    if row.data:
        d = row.data
        return RestaurantCard(
            place_id=d["place_id"],
            name=d["name"],
            rating=d["rating"],
            review_count=d["review_count"],
            price_level=d.get("price_level"),
            address=d.get("address", ""),
            photo_url=d.get("photo_url"),
            lat=d.get("lat"),
            lng=d.get("lng"),
        )

    # Fetch from Google Places Details
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        "X-Goog-Api-Key": settings.google_places_api_key,
        "X-Goog-FieldMask": (
            "id,displayName,rating,userRatingCount,priceLevel,"
            "formattedAddress,photos,location"
        ),
    }
    with httpx.Client(timeout=15) as http:
        resp = http.get(url, headers=headers)
        resp.raise_for_status()
        place = resp.json()

    photos = place.get("photos", [])
    photo_url = (
        _build_photo_url(photos[0]["name"], settings.google_places_api_key)
        if photos
        else None
    )
    location = place.get("location", {})
    price_map = {
        "PRICE_LEVEL_FREE": "$",
        "PRICE_LEVEL_INEXPENSIVE": "$",
        "PRICE_LEVEL_MODERATE": "$$",
        "PRICE_LEVEL_EXPENSIVE": "$$$",
        "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$",
    }
    price_raw = place.get("priceLevel")

    restaurant = RestaurantCard(
        place_id=place["id"],
        name=place["displayName"]["text"],
        rating=place.get("rating", 0),
        review_count=place.get("userRatingCount", 0),
        price_level=price_map.get(price_raw) if price_raw else None,
        address=place.get("formattedAddress", ""),
        photo_url=photo_url,
        lat=location.get("latitude"),
        lng=location.get("longitude"),
    )
    _cache_restaurants([restaurant])
    return restaurant
