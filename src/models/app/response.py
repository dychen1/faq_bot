from pydantic import BaseModel, Field


class RunETLResponse(BaseModel):
    successful: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
