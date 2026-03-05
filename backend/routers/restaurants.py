from fastapi import APIRouter, HTTPException, Query
from backend.models import RestaurantCard
from backend.services import google_places

router = APIRouter()


@router.get("/search", response_model=list[RestaurantCard])
def search_restaurants(
    city: str = Query(..., description="City to search in"),
    cuisine: str = Query("Any", description="Cuisine type"),
):
    try:
        return google_places.search_restaurants(city, cuisine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{place_id}", response_model=RestaurantCard)
def get_restaurant(place_id: str):
    restaurant = google_places.get_restaurant(place_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant
