from pydantic import BaseModel, Field

from src.utils.yelp import YelpBusinessData


class GetYelpDataResponse(BaseModel):
    data: list[YelpBusinessData]
    missing: list[str] = Field(default_factory=list)


class AnswerResponse(BaseModel):
    answer: str
