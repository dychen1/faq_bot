import logging
from typing import Any

from fastapi import HTTPException
from httpx import AsyncClient
from pydantic import BaseModel

from src.models.base import BusinessBase, BusinessLocation, BusinessTags, PriceLevel
from src.settings import settings

logger = logging.getLogger(settings.app_name)


class YelpBusinessSearchResponse(BaseModel):
    business_data: BusinessBase
    location_data: BusinessLocation
    business_attributes: BusinessTags


class YelpBusinessSearchParams(BaseModel):
    location_name: str
    zip_code: str
    phone_number: str | None = None
    area: str = "Bay Area"  # Default for demo dataset
    limit: int = 1  # Just want top relevant result for now
    sort_by: str = "best_match"

    @property
    def params(self) -> dict[str, str | int]:
        """
        sample valid query url: "https://api.yelp.com/v3/businesses/search?location=Bay%20Area%2C%204704&term=Fourn%C3%A9e%20Bakery&sort_by=best_match&limit=20"
        """
        params: dict[str, str | int] = {
            "location": f"{self.area},{self.zip_code}",
            "sort_by": self.sort_by,
            "limit": self.limit,
            "term": self.location_name,
        }

        # Add optional parameters
        if self.phone_number is not None:
            params["phone"] = self.phone_number
        return params  # No encoding here as we use httpx to run the query afterwards


class YelpBusinessSearch(BaseModel):
    client: AsyncClient
    base_url: str = f"{settings.yelp_base_url}/businesses/search"

    async def _get_data(self, params: YelpBusinessSearchParams) -> dict[str, Any]:
        logger.debug(f"Sending Yelp query with params: {params.params}")
        response = await self.client.get(
            self.base_url, params=params.params, headers={"Authorization": f"Bearer {settings.yelp_api_key}"}
        )
        logger.debug(f"Yelp response: {response.json()}")
        response.raise_for_status()
        return response.json()

    async def _parse_to_response_model(self, data: dict[str, Any]) -> YelpBusinessSearchResponse:
        # Get the first business from the response as we defaulted query limit to 1
        business = data["businesses"][0]

        # Parse business base data
        business_data = BusinessBase(
            name=business["name"],
            url=business["url"],
            price=PriceLevel(business["price"]),
            source="yelp",
            source_id=business["id"],
            source_url=business["url"],
            source_rating=business["rating"],
            phone=business["phone"],
        )

        # Parse location data
        location_data = BusinessLocation(
            longitude=business["coordinates"]["longitude"],
            latitude=business["coordinates"]["latitude"],
            address=business["location"]["address1"],
            city=business["location"]["city"],
            zip_code=business["location"]["zip_code"],
            country=business["location"]["country"],
            state=business["location"]["state"],
        )

        # Parse business attributes
        attributes = business["attributes"]
        ambience = attributes.get("ambience", {})
        good_for_meal = attributes.get("good_for_meal", {})
        business_parking = attributes.get("business_parking", {})

        business_attributes = BusinessTags(
            business_accepts_apple_pay=attributes.get("business_accepts_apple_pay") or False,
            business_temp_closed=attributes.get("business_temp_closed") or False,
            # Not sure what the possible enums are for alcohol attribute, so assuming anything other than "none" means the business serves alcohol
            alcohol=attributes.get("alcohol", "none") != "none",
            ambience_touristy=ambience.get("touristy") or False,
            ambience_hipster=ambience.get("hipster") or False,
            ambience_romantic=ambience.get("romantic") or False,
            ambience_divey=ambience.get("divey") or False,
            ambience_intimate=ambience.get("intimate") or False,
            ambience_trendy=ambience.get("trendy") or False,
            ambience_upscale=ambience.get("upscale") or False,
            ambience_classy=ambience.get("classy") or False,
            ambience_casual=ambience.get("casual") or False,
            bike_parking=attributes.get("bike_parking") or False,
            business_accepts_android_pay=attributes.get("business_accepts_android_pay") or False,
            business_accepts_credit_cards=attributes.get("business_accepts_credit_cards") or False,
            business_parking_garage=business_parking.get("garage") or False,
            business_parking_street=business_parking.get("street") or False,
            business_parking_validated=business_parking.get("validated") or False,
            business_parking_lot=business_parking.get("lot") or False,
            business_parking_valet=business_parking.get("valet") or False,
            caters=attributes.get("caters") or False,
            dogs_allowed=attributes.get("dogs_allowed") or False,
            good_for_kids=attributes.get("good_for_kids") or False,
            dessert=good_for_meal.get("dessert") or False,
            latenight=good_for_meal.get("latenight") or False,
            lunch=good_for_meal.get("lunch") or False,
            dinner=good_for_meal.get("dinner") or False,
            brunch=good_for_meal.get("brunch") or False,
            breakfast=good_for_meal.get("breakfast") or False,
            happy_hour=attributes.get("happy_hour") or False,
            has_tv=attributes.get("has_tv") or False,
            open24_hours=attributes.get("open24_hours") or False,
            restaurants_delivery=attributes.get("restaurants_delivery") or False,
            restaurants_good_for_groups=attributes.get("restaurants_good_for_groups") or False,
            restaurants_reservations=attributes.get("restaurants_reservations") or False,
            restaurants_table_service=attributes.get("restaurants_table_service") or False,
            restaurants_take_out=attributes.get("restaurants_take_out") or False,
            waitlist_reservation=attributes.get("waitlist_reservation") or False,
            wi_fi=attributes.get("wi_fi", "no") == "yes",
            has_gluten_free=attributes.get("has_gluten_free") or False,
            liked_by_vegetarians=attributes.get("liked_by_vegetarians") or False,
            liked_by_vegans=attributes.get("liked_by_vegans") or False,
            outdoor_seating=attributes.get("outdoor_seating") or False,
            hot_and_new=attributes.get("hot_and_new") or False,
        )

        return YelpBusinessSearchResponse(
            business_data=business_data, location_data=location_data, business_attributes=business_attributes
        )

    async def query(self, params: YelpBusinessSearchParams) -> YelpBusinessSearchResponse | None:
        try:
            yelp_data = await self._get_data(params)
            # Validate query response matches the business name
            if yelp_data["businesses"][0]["name"] != params.location_name:
                return None
            return await self._parse_to_response_model(yelp_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error querying Yelp: {e}")
