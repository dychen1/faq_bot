from pydantic import BaseModel


class BasicBusinessInfo(BaseModel):
    location_name: str
    zip_code: str
    phone_number: str | None = None


class GetYelpDataRequest(BaseModel):
    businesses: list[BasicBusinessInfo]
