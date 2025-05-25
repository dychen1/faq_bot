import json
from pathlib import Path
from typing import Any, Type

import aiofiles
from async_lru import alru_cache
from pydantic import ValidationError
from sqlalchemy.orm import DeclarativeBase

from src import PROMPT_PATH
from src.models.app.validation import ValidationModel


@alru_cache(maxsize=4)  # Cache up to 4 prompts
async def _load_prompt(path: Path) -> dict[str, str]:
    """Internal helper function to load a prompt from a JSON file asynchronously."""
    async with aiofiles.open(path, mode="r") as file:
        content = await file.read()
        return json.loads(content)


async def build_answer_generation_prompt(question: str, generated_sql: str, results: Any) -> tuple[str, str]:
    """
    Builds a prompt for generating an answer from a user question, generated SQL, and query results.

    Args:
        question: The user question to generate an answer for.
        generated_sql: The SQL query used to answer the question.
        results: The results of the SQL query.

    Returns:
        tuple[str, str]:
        A tuple containing (system prompt, user prompt) pair in that order.
    """
    prompt_path = PROMPT_PATH / "generate_answer"

    system_prompt_data = await _load_prompt(prompt_path / "system.json")
    system_prompt = system_prompt_data["message"]

    user_prompt_data = await _load_prompt(prompt_path / "user.json")
    user_prompt = user_prompt_data["message"].format(question=question, generated_sql=generated_sql, results=results)

    return system_prompt, user_prompt


async def build_response_fix_prompt(
    content: str, model: type[ValidationModel], error: ValidationError
) -> tuple[str, str]:
    """
    Constructs a prompt pair for fixing an invalid JSON output to a specified JSON schema.

    Args:
        content (str): The invalid JSON output to be fixed.
        model (type[ValidationModel]): The JSON schema to which the output should be fixed.
        error (ValidationError): The validation error from the original attempt
    Returns:
        tuple[str, str]:
        A tuple containing (system prompt, user prompt) pair in that order.
    """
    try:
        prompt_path = PROMPT_PATH / "validation"

        system_prompt_data = await _load_prompt(prompt_path / "system.txt")
        system_prompt = system_prompt_data["message"]

        user_prompt_data = await _load_prompt(prompt_path / "user.txt")
        user_prompt = user_prompt_data["message"].format(
            json_output=content, json_schema=model.model_json_schema(), error=error
        )

        return system_prompt, user_prompt

    except Exception as e:
        raise RuntimeError(
            f"Error in build_validation_prompt: {str(e)}. Ensure the prompt files exist, "
            f"contain the required keys ('message'), and the provided content and model are valid for formatting."
        )


async def build_sql_generation_prompt(
    question: str, dialect: str, models: list[Type[DeclarativeBase]]
) -> tuple[str, str]:
    """
    Builds a prompt for generating a SQL query from a user question, database dialect, and table schemas.
    Args:
        question: The user question to generate a SQL query for.
        dialect: The database dialect to use for the SQL query.
        models: A list of SQLAlchemy models to use for the SQL query.

    Returns:
        A tuple containing the system prompt and user prompt.
    """

    def _get_sqlalchemy_schema(model: Type[DeclarativeBase]) -> str:
        """
        Converts a SQLAlchemy model to a readable schema format for LLM prompts.

        Args:
            model: SQLAlchemy model class

        Returns:
            str: A formatted string representation of the table schema
        """
        schema_parts: list[str] = []

        # Get table name
        table_name: str = model.__tablename__
        schema_parts.append(f"Table: {table_name}")

        # Get columns
        columns: list[str] = []
        for column in model.__table__.columns:
            column_type: str = str(column.type)
            nullable: str = "NULL" if column.nullable else "NOT NULL"
            primary_key: str = "PRIMARY KEY" if column.primary_key else ""
            foreign_key: str = ""

            if column.foreign_keys:
                fk = list(column.foreign_keys)[0]
                foreign_key = f"REFERENCES {fk.target_fullname}"

            column_def = f"  {column.name} ({column_type}) {nullable} {primary_key} {foreign_key}".strip()
            columns.append(column_def)

        schema_parts.extend(columns)

        # Get relationships
        if hasattr(model, "__mapper__"):
            for rel in model.__mapper__.relationships:
                rel_type: str = "one-to-many" if rel.uselist else "one-to-one"
                schema_parts.append(f"  Relationship: {rel.key} ({rel_type}) -> {rel.target}")

        return "\n".join(schema_parts)

    # Convert models to schema strings
    schemas: str = "\n\n".join(_get_sqlalchemy_schema(model) for model in models)

    # HARD CODED TAGS FOR NOW -> TODO: fetch from db & implement caching + refresh cache on new tag entry to db
    tags = [
        "alcohol",
        "ambience_casual",
        "ambience_classy",
        "ambience_intimate",
        "ambience_romantic",
        "ambience_trendy",
        "ambience_upscale",
        "bike_parking",
        "breakfast",
        "brunch",
        "business_accepts_android_pay",
        "business_accepts_apple_pay",
        "business_accepts_credit_cards",
        "business_parking_garage",
        "business_parking_lot",
        "business_parking_street",
        "caters",
        "dinner",
        "dogs_allowed",
        "good_for_kids",
        "happy_hour",
        "has_gluten_free",
        "has_tv",
        "liked_by_vegans",
        "liked_by_vegetarians",
        "lunch",
        "outdoor_seating",
        "restaurants_delivery",
        "restaurants_good_for_groups",
        "restaurants_reservations",
        "restaurants_table_service",
        "restaurants_take_out",
        "waitlist_reservation",
        "wi_fi",
    ]
    prompt_path = PROMPT_PATH / "generate_sql"

    system_prompt_data = await _load_prompt(prompt_path / "system.json")
    system_prompt = system_prompt_data["message"]

    user_prompt_data = await _load_prompt(prompt_path / "user.json")
    user_prompt = user_prompt_data["message"].format(question=question, dialect=dialect, schemas=schemas, tags=tags)

    return system_prompt, user_prompt
