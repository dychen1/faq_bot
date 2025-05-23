from pydantic import BaseModel


class LoadDataBusinessInput(BaseModel):
    location_name: str
    zip_code: str
    phone_number: str | None = None


class LoadDataRequest(BaseModel):
    businesses: list[LoadDataBusinessInput]
