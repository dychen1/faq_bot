from enum import Enum

from pydantic import BaseModel

# Defined data models drives what data we want to pull from external API (e.g. Yelp, Google, etc.)


class PriceLevel(Enum):
    CHEAP = "$"
    MODERATE = "$$"
    EXPENSIVE = "$$$"
    VERY_EXPENSIVE = "$$$$"


class BusinessBase(BaseModel):
    name: str
    url: str
    price: PriceLevel
    source: str
    source_id: str | None
    source_url: str | None
    source_rating: float | None
    phone: str | None


class BusinessLocation(BaseModel):
    longitude: float
    latitude: float
    address: str
    city: str
    zip_code: str
    country: str
    state: str


class BusinessTags(BaseModel):
    business_accepts_apple_pay: bool
    business_temp_closed: bool
    alcohol: bool
    ambience_touristy: bool
    ambience_hipster: bool
    ambience_romantic: bool
    ambience_divey: bool
    ambience_intimate: bool
    ambience_trendy: bool
    ambience_upscale: bool
    ambience_classy: bool
    ambience_casual: bool
    bike_parking: bool
    business_accepts_android_pay: bool
    business_accepts_credit_cards: bool
    business_parking_garage: bool
    business_parking_street: bool
    business_parking_validated: bool
    business_parking_lot: bool
    business_parking_valet: bool
    caters: bool
    dogs_allowed: bool
    good_for_kids: bool
    dessert: bool
    latenight: bool
    lunch: bool
    dinner: bool
    brunch: bool
    breakfast: bool
    happy_hour: bool
    has_tv: bool
    # noise_level: Enum # Not sure what the possible enums are for this, so skipping this attribute for now
    open24_hours: bool
    # platform_delivery: Enum # Not sure what the possible enums are for this, so skipping this attribute for now
    restaurants_delivery: bool
    restaurants_good_for_groups: bool
    restaurants_reservations: bool
    restaurants_table_service: bool
    restaurants_take_out: bool
    waitlist_reservation: bool
    wi_fi: bool
    has_gluten_free: bool
    liked_by_vegetarians: bool
    liked_by_vegans: bool
    outdoor_seating: bool
    hot_and_new: bool
