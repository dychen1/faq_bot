from typing import TypeVar

from pydantic import BaseModel

ValidationModel = TypeVar("ValidationModel", bound=BaseModel)


class GeneratedSQL(BaseModel):
    generated_sql: str
