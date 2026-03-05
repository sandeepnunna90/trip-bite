from fastapi import APIRouter, HTTPException, Depends
from backend.models import Trip, TripRestaurant, TripDetail, AddRestaurantRequest, CreateTripRequest, RestaurantCard, Dish
from backend.routers.auth import get_current_user
from backend.services.supabase_client import get_anon_client, get_service_client

router = APIRouter()


def _authed_client(user: dict):
    """Get Supabase client with user's JWT for RLS enforcement."""
    from supabase import create_client
    from backend.config import get_settings
    s = get_settings()
    client = create_client(s.supabase_url, s.supabase_anon_key)
    client.auth.set_session(user["token"], "")
    return client


@router.post("", response_model=Trip)
def create_trip(req: CreateTripRequest, user: dict = Depends(get_current_user)):
    client = get_service_client()
    result = client.table("trips").insert({
        "user_id": user["user_id"],
        "name": req.name,
    }).execute()
    row = result.data[0]
    return Trip(id=row["id"], user_id=row["user_id"], name=row["name"], created_at=row["created_at"])


@router.get("/me", response_model=list[Trip])
def get_my_trips(user: dict = Depends(get_current_user)):
    client = get_service_client()
    result = client.table("trips").select("*").eq("user_id", user["user_id"]).execute()
    return [Trip(id=r["id"], user_id=r["user_id"], name=r["name"], created_at=r["created_at"]) for r in result.data]


@router.get("/{trip_id}", response_model=TripDetail)
def get_trip(trip_id: str, user: dict = Depends(get_current_user)):
    client = get_service_client()

    trip_result = client.table("trips").select("*").eq("id", trip_id).eq("user_id", user["user_id"]).maybe_single().execute()
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


@router.post("/{trip_id}/restaurants")
def add_restaurant(trip_id: str, req: AddRestaurantRequest, user: dict = Depends(get_current_user)):
    client = get_service_client()

    trip_check = client.table("trips").select("id").eq("id", trip_id).eq("user_id", user["user_id"]).maybe_single().execute()
    if not trip_check.data:
        raise HTTPException(status_code=403, detail="Trip not found or access denied")

    try:
        client.table("trip_restaurants").insert({
            "trip_id": trip_id,
            "place_id": req.place_id,
        }).execute()
    except Exception as e:
        if "unique" in str(e).lower():
            return {"message": "Already in trip"}
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Added to trip"}


@router.delete("/{trip_id}/restaurants/{place_id}")
def remove_restaurant(trip_id: str, place_id: str, user: dict = Depends(get_current_user)):
    client = get_service_client()

    trip_check = client.table("trips").select("id").eq("id", trip_id).eq("user_id", user["user_id"]).maybe_single().execute()
    if not trip_check.data:
        raise HTTPException(status_code=403, detail="Trip not found or access denied")

    client.table("trip_restaurants").delete().eq("trip_id", trip_id).eq("place_id", place_id).execute()
    return {"message": "Removed from trip"}
