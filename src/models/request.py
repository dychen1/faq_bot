from pydantic import BaseModel


class BusinessInput(BaseModel):
    location_name: str
    zip_code: str
    phone_number: str | None = None


class RunETLRequest(BaseModel):
    businesses: list[BusinessInput]
