from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.routers.auth import get_current_user
from backend.services.supabase_client import get_service_client
from backend.models import TripDetail, TripRestaurant, RestaurantCard, Dish
from backend.config import get_settings

router = APIRouter()


class CreateShareRequest(BaseModel):
    trip_id: str


@router.post("")
def create_share(req: CreateShareRequest, user: dict = Depends(get_current_user)):
    client = get_service_client()
    settings = get_settings()

    trip_check = client.table("trips").select("id").eq("id", req.trip_id).eq("user_id", user["user_id"]).maybe_single().execute()
    if not trip_check.data:
        raise HTTPException(status_code=403, detail="Trip not found or access denied")

    # Check for existing token
    existing = client.table("share_tokens").select("token").eq("trip_id", req.trip_id).execute()
    if existing.data:
        token = existing.data[0]["token"]
    else:
        result = client.table("share_tokens").insert({"trip_id": req.trip_id}).execute()
        token = result.data[0]["token"]

    frontend_url = settings.backend_url.replace(":8000", ":8501").rstrip("/")
    share_url = f"{frontend_url}/Shared_Trip?token={token}"
    return {"token": token, "share_url": share_url}


@router.get("/{token}", response_model=TripDetail)
def get_shared_trip(token: str):
    client = get_service_client()

    token_result = client.table("share_tokens").select("*").eq("token", token).maybe_single().execute()
    if not token_result.data:
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    trip_id = token_result.data["trip_id"]
    trip_result = client.table("trips").select("*").eq("id", trip_id).maybe_single().execute()
    if not trip_result.data:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip = trip_result.data

    tr_result = client.table("trip_restaurants").select("*").eq("trip_id", trip_id).execute()

    restaurants: list[TripRestaurant] = []
    for tr in tr_result.data:
        place_id = tr["place_id"]
        rc = client.table("restaurant_cache").select("*").eq("place_id", place_id).maybe_single().execute()
        dc = client.table("dish_cache").select("*").eq("place_id", place_id).execute()

        restaurant = None
        if rc.data:
            d = rc.data
            restaurant = RestaurantCard(
                place_id=d["place_id"], name=d["name"], rating=d["rating"],
                review_count=d["review_count"], price_level=d.get("price_level"),
                address=d.get("address", ""), photo_url=d.get("photo_url"),
                lat=d.get("lat"), lng=d.get("lng"),
            )

        dishes = [
            Dish(dish_name=row["dish_name"], reason=row["reason"],
                 is_vegetarian=row["is_vegetarian"], confidence=row["confidence"])
            for row in dc.data
        ] if dc.data else []

        restaurants.append(TripRestaurant(
            id=tr["id"], trip_id=tr["trip_id"], place_id=place_id,
            added_at=tr["added_at"], restaurant=restaurant, dishes=dishes,
        ))

    return TripDetail(id=trip["id"], name=trip["name"], restaurants=restaurants)
