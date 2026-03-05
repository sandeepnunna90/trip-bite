from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RestaurantCard(BaseModel):
    place_id: str
    name: str
    rating: float
    review_count: int
    price_level: Optional[str] = None
    address: str
    photo_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class Dish(BaseModel):
    dish_name: str
    reason: str
    is_vegetarian: bool
    confidence: str  # "high" | "medium" | "low"


class Trip(BaseModel):
    id: str
    user_id: str
    name: str
    created_at: datetime


class TripRestaurant(BaseModel):
    id: str
    trip_id: str
    place_id: str
    added_at: datetime
    restaurant: Optional[RestaurantCard] = None
    dishes: Optional[list[Dish]] = None


class TripDetail(BaseModel):
    id: str
    name: str
    restaurants: list[TripRestaurant]


class ShareToken(BaseModel):
    token: str
    trip_id: str
    share_url: str


class AuthResponse(BaseModel):
    access_token: str
    user_id: str


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class CreateTripRequest(BaseModel):
    name: str


class AddRestaurantRequest(BaseModel):
    place_id: str
