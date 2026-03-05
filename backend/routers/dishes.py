from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta, timezone
from backend.models import Dish
from backend.services.apify_service import get_reviews
from backend.services.claude_ai import extract_dishes
from backend.services.supabase_client import get_service_client

router = APIRouter()

DISH_CACHE_DAYS = 7


def _get_cached_dishes(place_id: str) -> list[Dish] | None:
    client = get_service_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=DISH_CACHE_DAYS)).isoformat()
    result = (
        client.table("dish_cache")
        .select("*")
        .eq("place_id", place_id)
        .gte("cached_at", cutoff)
        .execute()
    )
    if not result.data:
        return None
    return [
        Dish(
            dish_name=row["dish_name"],
            reason=row["reason"],
            is_vegetarian=row["is_vegetarian"],
            confidence=row["confidence"],
        )
        for row in result.data
    ]


def _cache_dishes(place_id: str, dishes: list[Dish]) -> None:
    client = get_service_client()
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        {
            "place_id": place_id,
            "dish_name": d.dish_name,
            "reason": d.reason,
            "is_vegetarian": d.is_vegetarian,
            "confidence": d.confidence,
            "cached_at": now,
        }
        for d in dishes
    ]
    client.table("dish_cache").upsert(rows).execute()


@router.get("/{place_id}", response_model=list[Dish])
def get_dishes(place_id: str):
    cached = _get_cached_dishes(place_id)
    if cached:
        return cached

    try:
        reviews = get_reviews(place_id)
        if not reviews:
            raise HTTPException(status_code=404, detail="No reviews found for this restaurant")

        dishes = extract_dishes(reviews)
        _cache_dishes(place_id, dishes)
        return dishes
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
